#!/usr/local/bin/python3
# Copyright 2017 Nate Bogdanowicz, Julia Westbom

import sys
import os
from enum import Enum
from attr import attrs, attrib, validators, asdict

from ui import mainwindow_ui
from ui import dialog_drink_builder_ui
from ui import ing_dialog_uid

from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QDialog, QTableWidgetItem
from PyQt5.QtCore import Qt

import json


class Style(Enum):
    Built = 0
    Stirred = 1
    Shaken = 2

@attrs
class Liquid:
    name = attrib()
    abv = attrib(validator=validators.instance_of(float))
    sugar = attrib(validator=validators.instance_of(float))
    acid = attrib(validator=validators.instance_of(float))

@attrs
class Pour:
    liquid = attrib()
    ounces = attrib()

class Drink:
    def __init__(self, name, pours, style):
        self.name = name
        self.pours = [mk_pour(**args) for args in pours]
        self.style = Style[style]

        tot_alc = sum((p.ounces*p.liquid.abv for p in self.pours))
        tot_sug = sum((p.ounces*p.liquid.sugar for p in self.pours))
        tot_acd = sum((p.ounces*p.liquid.acid for p in self.pours))

        self.start_ounces = sum((pour.ounces for pour in self.pours))
        self.start_abv = tot_alc / self.start_ounces
        self.start_sugar = tot_sug / self.start_ounces
        self.start_acid = tot_acd / self.start_ounces

        if self.style == Style.Stirred:
            dilution_ratio = -1.21 * self.start_abv**2 + 1.246 * self.start_abv + 0.145
        elif self.style == Style.Shaken:
            dilution_ratio = 1.567 * self.start_abv**2 + 1.742 * self.start_abv + 0.203
        else:
            raise NotImplementedError

        water_ounces = self.start_ounces * dilution_ratio

        self.ounces = self.start_ounces + water_ounces
        self.abv = tot_alc / self.ounces
        self.sugar = tot_sug / self.ounces
        self.acid = tot_acd / self.ounces


def show_drink_stats(current, previous):
    new_drink = current.text()
    drink_atts = drinks[new_drink]
    ui.label_drink_name.setText(drink_atts.name)
    ui.label_drink_abv.setText(f'{drink_atts.abv * 100 :.2f}%')
    ui.label_drink_sugar.setText(f'{drink_atts.sugar * 100 :.2f}%')
    ui.label_drink_acid.setText(f'{drink_atts.acid * 100 :.2f}%')

    ui.list_liquids.clear()
    for pour in drink_atts.pours:
        ingred = f'{pour.ounces} oz {pour.liquid.name}'
        item = QListWidgetItem(ingred)
        ui.list_liquids.addItem(item)


def show_ing_stats(current, previous):
    if current:
        new_ing = current.text()
        ing_atts = liquids[new_ing]
        ui.lineEdit_ing_name.setText(ing_atts.name)
        ui.lineEdit_ing_abv.setText(f'{ing_atts.abv * 100}')
        ui.lineEdit_ing_sugar.setText(f'{ing_atts.sugar * 100}')
        ui.lineEdit_ing_acid.setText(f'{ing_atts.acid * 100}')


def save_ingredient():
    try:
        name = ui.lineEdit_ing_name.text()
        abv = float(ui.lineEdit_ing_abv.text()) / 100
        sugar = float(ui.lineEdit_ing_sugar.text()) / 100
        acid = float(ui.lineEdit_ing_acid.text()) / 100
        liquid = Liquid(name, abv, sugar, acid)
    except:
        raise ValueError('Invalid liquid')

    if ui.list_ingredients.currentItem():  # If ingredient selected, check if name changed
        if ui.list_ingredients.currentItem().text() == name:
            print('Updating', name)
        else:
            print('Really should check if this is an update or an add')
    liquids[name] = liquid
    write_user_data(liquids, liquids_file)
    item = QListWidgetItem(name)
    ui.list_ingredients.addItem(item)
    ui.list_ingredients.setCurrentItem(item)
    ui.list_ingredients.sortItems()


def refresh_ingredient_list():
    ui.list_ingredients.clear()
    for i in liquids:
        item = QListWidgetItem(i)
        ui.list_ingredients.addItem(item)
    ui.list_ingredients.sortItems()
    ui.list_ingredients.setCurrentItem(ui.list_ingredients.item(0))
    print('here')


def add_ingredient():
    ui.lineEdit_ing_name.clear()
    ui.lineEdit_ing_abv.clear()
    ui.lineEdit_ing_sugar.clear()
    ui.lineEdit_ing_acid.clear()
    ui.lineEdit_ing_name.setFocus()
    ui.list_ingredients.setCurrentRow(-1)
    print('Add Me!')


def del_ingredient():
    try:
        name = ui.lineEdit_ing_name.text()
    except:
        raise ValueError('Invalid liquid')

    if ui.list_ingredients.currentItem():  # If ingredient selected, check if name changed
        if ui.list_ingredients.currentItem().text() == name:
            print('Updating', name)
        else:
            print('Really should check if this is an update or an add')
    if name in liquids:
        del liquids[name]
    write_user_data(liquids, liquids_file)
    refresh_ingredient_list()

    print('Deleted!')


def refresh_drink_builder(drink):
    drink_ui.lineEdit_drink_name.setText(drink.name)
    drink_ui.label_abv.setText(f'{drink.abv * 100 :.2f}')
    drink_ui.label_acid.setText(f'{drink.acid * 100 :.2f}')
    drink_ui.label_sugar.setText(f'{drink.sugar * 100 :.2f}')
    if drink.style == Style.Stirred:
        drink_ui.radioButton_stirred.setChecked(True)
        drink_ui.radioButton_shaken.setChecked(False)
    elif drink.style == Style.Shaken:
        drink_ui.radioButton_stirred.setChecked(False)
        drink_ui.radioButton_shaken.setChecked(True)

    row = 0
    drink_ui.tableWidget_drink_ing.setRowCount(len(drink.pours))
    drink_ui.tableWidget_drink_ing.clearContents()
    for pour in drink.pours:
        name = QTableWidgetItem(pour.liquid.name)
        abv = QTableWidgetItem(f'{pour.liquid.abv * 100 :.2f}%')
        sugar = QTableWidgetItem(f'{pour.liquid.sugar * 100 :.2f}%')
        acid = QTableWidgetItem(f'{pour.liquid.acid * 100 :.2f}%')
        oz = QTableWidgetItem(f'{pour.ounces :.1f}')
        name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        abv.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        sugar.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        acid.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        drink_ui.tableWidget_drink_ing.setItem(row, 0, name)
        drink_ui.tableWidget_drink_ing.setItem(row, 1, oz)
        drink_ui.tableWidget_drink_ing.setItem(row, 2, abv)
        drink_ui.tableWidget_drink_ing.setItem(row, 3, sugar)
        drink_ui.tableWidget_drink_ing.setItem(row, 4, acid)
        row += 1



def write_user_data(data, file):
    json_data = [asdict(data[d]) for d in data]
    with open(file, 'w') as f:
        json.dump(json_data, f)


def mk_pour(name, ounces):
    liquid = liquids[name]
    return Pour(liquid, ounces)


def add_drink():
    win_drink.show()
    print('make me something tasty')


def edit_drink():
    current_drink = ui.list_drinks.currentItem().text()
    drink_ui.lineEdit_drink_name.setText(current_drink)
    refresh_drink_builder(drinks[current_drink])

    win_drink.show()
    print('edit drink')


if __name__ == '__main__':
    liquids_file = os.path.join('user_data', 'liquids.json')
    drinks_file = os.path.join('user_data', 'drinks.json')

    # ----- Load Data -----

    with open('liquids.json', 'r') as f:
        data = json.load(f)
    if os.path.isfile(liquids_file):
        with open(liquids_file, 'r') as f:
            data.extend(json.load(f))
    liquids = {d['name']:Liquid(**d) for d in data}
    with open('drinks.json', 'r') as f:
        data = json.load(f)
    drinks = {d['name']:Drink(**d) for d in data}

    # ----- Create App ------

    app = QApplication(sys.argv)

    # ----- Main Window ------

    win = QMainWindow()
    ui = mainwindow_ui.Ui_MainWindow()
    ui.setupUi(win)

    for d in drinks:
        item = QListWidgetItem(d)
        ui.list_drinks.addItem(item)
    ui.list_drinks.sortItems()

    ui.list_drinks.currentItemChanged.connect(show_drink_stats)
    ui.list_ingredients.currentItemChanged.connect(show_ing_stats)
    ui.pushButton_ing_save.clicked.connect(save_ingredient)
    ui.pushButton_ing_add.clicked.connect(add_ingredient)
    ui.pushButton_ing_del.clicked.connect(del_ingredient)
    ui.pushButton_add_drink.clicked.connect(add_drink)
    ui.pushButton_edit_drink.clicked.connect(edit_drink)

    refresh_ingredient_list()

    # ----- Drink Builder Dialog -----

    win_drink = QDialog()
    drink_ui = dialog_drink_builder_ui.Ui_Dialog()
    drink_ui.setupUi(win_drink)
    drink_ui.tableWidget_drink_ing.setColumnCount(5)
    drink_ui.tableWidget_drink_ing.setHorizontalHeaderLabels(['Ingredient', 'Quantity','ABV','Sugar','Acid'])

    # ----- Show Main Window -----
    win.show()
    app.exec_()
