import sys
import time
import math
import time
import os
import random
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from struct import *
from io import StringIO
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QListWidgetItem, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from LZCompressor import Ui_MainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class Compressor(QtWidgets.QMainWindow):

    def __init__(self):
        super(Compressor, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.input_file_name = ''
        self.output_file_name = ''

        self.ui.pushButton.clicked.connect(self.file_btn_click)
        self.ui.compButton.clicked.connect(self.compress_btn_click)
        self.ui.dirButton.clicked.connect(self.saveFileDialog)
        self.ui.decompButton.clicked.connect(self.decompress_btn_click)
        self.ui.comp_decomp_btn.clicked.connect(self.analise_click)

        self.clear_table()

    def autolabel(self, rects, ax, rotation):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height/2),
                        xytext=(0, 3), 
                        textcoords="offset points",
                        ha='center', va='bottom',
                        rotation=rotation)

    def show_one_graph(self, uncomp, comp):
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ui.verticalLayout.addWidget(self.canvas)

        color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        axs = self.figure.subplots(gridspec_kw={'right':0.9, 'left':0.2})
        axs.set_title('Default/Compressed')
        axs.set_ylabel('Size, Kb')
        rects = axs.bar(['Default', 'Compressed'], [uncomp, comp], color=color)
        self.autolabel(rects, axs, 0)
        
    def show_graphs(self, size, comp_time, decomp_time, coeff):

        self.figure = plt.figure()
        self.figure0 = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas_0 = FigureCanvas(self.figure0)
        self.ui.verticalLayout.addWidget(self.canvas)
        self.ui.verticalLayout.addWidget(self.canvas_0)

        size_names = list(size.keys())
        size_values = list(size.values())

        comp_time_names = list(comp_time.keys())
        comp_time_values = list(comp_time.values())

        decomp_time_names = list(decomp_time.keys())
        decomp_time_values = list(decomp_time.values())

        coeff_names = list(coeff.keys())
        coeff_values = list(coeff.values())

        width = 0.6
        axs = self.figure.subplots(1, 2, gridspec_kw={'wspace':0.3, 'right':0.97})
        rects1 = axs[0].bar(size_names, size_values, color='red', width=width)
        axs[0].set_title('Compressed Sizes')
        axs[0].set_ylabel('Size, Kb')
        rects2 = axs[1].bar(coeff_names, coeff_values, color='green', width=width)
        axs[1].set_title('Compression Ratio')

        axs0 = self.figure0.subplots(1, 2, gridspec_kw={'wspace':0.3, 'right':0.97})        
        rects0_1 = axs0[0].bar(comp_time_names, comp_time_values, color='blue', width=width)
        axs0[0].set_title('Compressing')
        axs0[0].set_ylabel('Time, sec')
        rects0_2 = axs0[1].bar(decomp_time_names, decomp_time_values, color='yellow', width=width)
        axs0[1].set_title('Decompressing')
        self.figure0.suptitle('Time')

        self.autolabel(rects1, axs[0], 90)
        self.autolabel(rects2, axs[1], 90)

        self.autolabel(rects0_1, axs0[0], 90)
        self.autolabel(rects0_2, axs0[1], 90)

        self.canvas.draw()
        self.canvas_0.draw()

    def clear_table(self):

        self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(3)
        self.ui.tableWidget.setColumnCount(6)
        self.ui.tableWidget.setHorizontalHeaderLabels(
            ('Uncompressed', 'Compressed', 'Compression Ratio', 'Compression Time', 'Decompression Time', ' Size Percentage ')
        )

        self.ui.tableWidget.setVerticalHeaderLabels(
            ('LZW', 'LZ77', 'LZ78')
        )

        self.ui.tableWidget.resizeColumnsToContents()

    def clear_graphs(self):
        for i in reversed(range(self.ui.verticalLayout.count())): 
            widgetToRemove = self.ui.verticalLayout.itemAt(i).widget()
            self.ui.verticalLayout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

    def analise_click(self):

        self.ui.infoLabel.setText('')
        file = self.input_file_name.replace('Compressor', '')
        self.clear_graphs()
        self.ui.checkBoxW.setChecked(True)
        self.ui.checkBox77.setChecked(True)
        self.ui.checkBox78.setChecked(True)

        uncompressedW, compressedW, ratio_w, c_stop_time_w, percantage_w, steps_w = \
            self.compressW(self.ui.textEdit.toPlainText(), self.ui.spinBox_LZW.value(), self.output_file_name)
        _, _, _, d_stop_time_w, _ = self.decompressW(self.input_file_name + '.lzw', self.ui.spinBox_LZW.value())
        self.ui.listWidget.clear()
        self.show_one_table_row([uncompressedW, compressedW, ratio_w, c_stop_time_w, d_stop_time_w, percantage_w], 0)
        self.show_steps(steps_w, 1)

        uncompressed77, compressed77, ratio_77, c_stop_time_77, percantage_77, steps_77 = \
            self.compress77(self.ui.textEdit.toPlainText(), self.ui.spinBox_LZ77.value(), self.output_file_name)
        _, _, _, d_stop_time_77, _ = self.decompress77(self.input_file_name + '.lz77', self.ui.spinBox_LZ77.value())
        self.ui.listWidget.clear()
        self.show_one_table_row([uncompressed77, compressed77, ratio_77, c_stop_time_77, d_stop_time_77, percantage_77], 1)
        self.show_steps(steps_w, 1)
        self.ui.listWidget_2.clear()
        self.show_steps(steps_77, 2)

        uncompressed78, compressed78, ratio_78, c_stop_time_78, percantage_78, steps_78 = \
            self.compress78(self.ui.textEdit.toPlainText(), self.output_file_name)
        _, _, _, d_stop_time_78, _ = self.decompress78(self.input_file_name + '.lz78')
        self.ui.listWidget_3.clear()
        self.show_one_table_row([uncompressed78, compressed78, ratio_78, c_stop_time_78, d_stop_time_78, percantage_78], 2)
        self.show_steps(steps_78, 3)

        sizes = {
            'Default': round(os.path.getsize(file + '.txt')/1024, 1), 
            'LZW': round(compressedW/1024, 1), 
            'LZ77': round(compressed77/1024, 1),
            'LZ78': round(compressed78/1024, 1)
        }
        comp_times = {
            'LZW': round(c_stop_time_w, 1), 
            'LZ77': round(c_stop_time_77, 1), 
            'LZ78': round(c_stop_time_78, 1)
        }
        decomp_times = {
            'LZW': round(d_stop_time_w,1), 
            'LZ77': round(d_stop_time_77, 1), 
            'LZ78': round(d_stop_time_78, 1)
        }
        coeff = {
            'LZW': round(ratio_w, 1), 
            'LZ77': round(ratio_77, 1), 
            'LZ78': round(ratio_78, 1)
        }

        self.show_graphs(sizes, comp_times, decomp_times, coeff)
        self.ui.tableWidget.resizeColumnsToContents()
        
    def show_one_table_row(self, data, row):

        i = 0
        data[-1] = round(data[-1], 10)
        for item in data:
                cellinfo = QTableWidgetItem(str(item))
                cellinfo.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.ui.tableWidget.setItem(row, i, cellinfo)
                i+=1

    def show_steps(self, data, number):

        if number == 1:
            for step in data:
                item = QtWidgets.QListWidgetItem()
                item.setText(str(step[0]) + ': <' + str(step[1])+ ', ' + str(step[2]) + '>')
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                self.ui.listWidget.addItem(item)
        elif number == 2:
            for step in data:
                item = QtWidgets.QListWidgetItem()
                item.setText('<' + str(step[0]) + ', ' + str(step[1])+ ', ' + str(step[2]) + '>')
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                self.ui.listWidget_2.addItem(item)
        else:
            for step in data:
                item = QtWidgets.QListWidgetItem()
                item.setText(str(step[0]) + ': <' + str(step[1]) + '>')
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                self.ui.listWidget_3.addItem(item)            

    def compress_btn_click(self):
        
        self.ui.infoLabel.setText('')
        try:
            self.clear_graphs()
            self.clear_table()
            self.ui.listWidget.clear()
            self.ui.listWidget_3.clear()
            self.ui.listWidget_2.clear()

            if self.ui.checkBoxW.isChecked():
                data_w = self.compressW(self.ui.textEdit.toPlainText(), self.ui.spinBox_LZW.value(), self.output_file_name)
                new_data = list(data_w)
                new_data.insert(4, '- '*15)
                self.show_steps(new_data[6], 1)
                self.show_one_graph(data_w[0], data_w[1])
                self.show_one_table_row(new_data[:6], 0)
            if self.ui.checkBox77.isChecked():
                data_77 = self.compress77(self.ui.textEdit.toPlainText(), self.ui.spinBox_LZ77.value(), self.output_file_name)
                new_data = list(data_77)
                new_data.insert(4, '- '*15)
                self.show_steps(new_data[6], 2)
                self.show_one_graph(data_77[0], data_77[1])
                self.show_one_table_row(new_data[:6], 1)
            if self.ui.checkBox78.isChecked():
                data_78 = self.compress78(self.ui.textEdit.toPlainText(), self.output_file_name)
                new_data = list(data_78)
                new_data.insert(4, '- '*15)
                self.show_steps(new_data[6], 3)
                self.show_one_graph(data_78[0], data_78[1])
                self.show_one_table_row(new_data[:6], 2)
            
            if not self.ui.checkBoxW.isChecked() and not self.ui.checkBox77.isChecked() and not self.ui.checkBox78.isChecked():
                self.ui.infoLabel.setText('None of algorithms is chosen\nChose one of the algorithm to continue!')

            self.ui.tableWidget.resizeColumnsToContents()
        except:
            self.ui.infoLabel.setText('Something went wrong...\nCheck settings and try again!')

    def decompress_btn_click(self):
        
        self.ui.infoLabel.setText('')
        try:
            self.clear_graphs()
            self.clear_table()
            self.ui.listWidget.clear()
            self.ui.listWidget_3.clear()
            self.ui.listWidget_2.clear()

            if self.ui.checkBoxW.isChecked():
                data_w = self.decompressW(self.input_file_name, self.ui.spinBox_LZW.value())
                new_list = list(data_w)
                new_list.insert(3, '- '*15)
                self.show_one_graph(data_w[0], data_w[1])
                self.show_one_table_row(new_list, 0)
            if self.ui.checkBox78.isChecked():
                data_78 = self.decompress78(self.input_file_name)
                new_list = list(data_78)
                new_list.insert(3, '- '*15)
                self.show_one_graph(data_78[0], data_78[1])
                self.show_one_table_row(new_list, 2)
            if self.ui.checkBox77.isChecked():
                data_77 = self.decompress77(self.input_file_name, self.ui.spinBox_LZ77.value())
                new_list = list(data_77)
                new_list.insert(3, '- '*15)
                self.show_one_graph(data_77[0], data_77[1])
                self.show_one_table_row(new_list, 1)

            if not self.ui.checkBoxW.isChecked() and not self.ui.checkBox77.isChecked() and not self.ui.checkBox78.isChecked():
                self.ui.infoLabel.setText('None of algorithms is chosen\nChose one of the algorithm to continue!')

            self.ui.tableWidget.resizeColumnsToContents()
        except:
            self.ui.infoLabel.setText('Something went wrong...\nCheck settings and try again!')


    def file_btn_click(self):

        self.ui.infoLabel.setText('')
        self.ui.checkBoxW.setChecked(False)
        self.ui.checkBox78.setChecked(False)
        self.ui.checkBox77.setChecked(False)
        try:
            file_name = self.openFileNameDialog()
            if file_name[-4:] == '.lzw':
                self.ui.textEdit.setText('Decompress: ' + file_name)
                self.ui.checkBoxW.setChecked(True)
                self.input_file_name = file_name
            elif file_name[-5:] == '.lz77':
                self.ui.textEdit.setText('Decompress: ' + file_name)
                self.ui.checkBox77.setChecked(True)
                self.input_file_name = file_name
            elif file_name[-5:] == '.lz78':
                self.ui.checkBox78.setChecked(True)
                self.input_file_name = file_name
                self.ui.textEdit.setText('Decompress: ' + file_name)
            else:
                try:
                    with open(file_name, 'r') as file:
                        self.ui.textEdit.setText(file.read())
                except:
                    with open(file_name, 'r', encoding='utf-8') as file:
                        self.ui.textEdit.setText(file.read())
        except:
            file_name = ''

    def openFileNameDialog(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Choose File", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            self.output_file_name = fileName.replace('.txt', '').replace('.lzw', '').replace('.lz78', '').replace('.lz77', '').replace('Compressor', '') + 'Compressor'
            self.ui.outEdit.setText(self.output_file_name)
            self.input_file_name = fileName.replace('.txt', '') + 'Compressor'
            return fileName
    
    def saveFileDialog(self):
        
        self.ui.infoLabel.setText('')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dirName = QFileDialog.getExistingDirectory(self, "Choose directory", options=options) 
        if dirName:
            if self.input_file_name:
                self.output_file_name = dirName + '/' + self.input_file_name
            else:
                self.output_file_name = dirName + '/Compressor'
            self.ui.outEdit.setText(self.output_file_name)

    def LZ77_search(self, search, look_ahead):
    
        ls = len(search)
        llh = len(look_ahead)

        if(ls==0):
            return (0,0, look_ahead[0])
        if(llh)==0:
            return (-1,-1,"")

        best_length=0
        best_offset=0 
        buf = search + look_ahead

        search_pointer = ls	
        for i in range(0,ls):
            length = 0
            while buf[i+length] == buf[search_pointer +length]:
                length = length + 1
                if search_pointer+length == len(buf):
                    length = length - 1
                    break
                if i+length >= search_pointer:
                    break	 
            if length > best_length:
                best_offset = i
                best_length = length

        return (best_offset, best_length, buf[search_pointer+best_length])

    def compress77(self, input, win_size, output_file):
        start_time = time.time()
        #extra credit
        x = 16
        MAXSEARCH = int(win_size)
        MAXLH =  int(math.pow(2, (x  - (math.log(MAXSEARCH, 2))))) 
        file = open(output_file + '.lz77', "wb")
        searchiterator, lhiterator = 0, 0;
        steps = []
        while lhiterator<len(input):
            search = input[searchiterator:lhiterator]
            look_ahead = input[lhiterator:lhiterator+MAXLH]
            (offset, length, char) = self.LZ77_search(search, look_ahead)
            steps.append([offset, length, char])
            shifted_offset = offset << 6
            offset_and_length = shifted_offset+length 
            placeholder = ' '
            try:
                ol_bytes = pack(">Hc",offset_and_length, bytes(char, 'utf-8'))  
            except:
                ol_bytes = pack(">Hc",offset_and_length, bytes(placeholder, 'utf-8')) 
            file.write(ol_bytes) 
            
            lhiterator = lhiterator + length+1
            searchiterator = lhiterator - MAXSEARCH

            if searchiterator<0:
                searchiterator=0
                
        file.close()

        return os.path.getsize(output_file.replace('Compressor', '') + '.txt'), \
               os.path.getsize(output_file + '.lz77'), os.path.getsize(output_file.replace('Compressor', '') + '.txt')/\
               os.path.getsize(output_file + '.lz77'), time.time() - start_time, os.path.getsize(output_file + '.lz77')/\
               os.path.getsize(output_file.replace('Compressor', '') + '.txt')*100, steps
        

    def decompress77(self, input_file, search):
        
        start_time = time.time()
        try:
            processed = open(self.output_file_name + 'LZ77.txt', "wb")
        except:
            processed = open(self.output_file_name + 'LZ77.txt', "wb", encoding='utf-8')

        MAX_SEARCH = search
        file = open(input_file, "rb") 
        input = file.read() 
        chararray = bytearray()
        i=0

        while i<len(input):
            (offset_and_length, char) = unpack(">Hc", input[i:i+3])
            offset = offset_and_length >> 6
            length = offset_and_length - (offset<<6)
            i=i+3
            if(offset == 0) and (length == 0):
                chararray += char
            else:
                iterator = len(chararray) - MAX_SEARCH
                if iterator <0:
                    iterator = offset
                else:
                    iterator += offset
                for pointer in range(length):
                    chararray += bytes(chr(chararray[iterator+pointer]), 'utf-8')
                chararray += char
        processed.write(chararray) 

        return os.path.getsize(self.output_file_name + 'LZ77.txt'), \
               os.path.getsize(input_file), os.path.getsize(self.output_file_name + 'LZ77.txt')/\
               os.path.getsize(input_file), time.time() - start_time, os.path.getsize(input_file)/\
               os.path.getsize(self.output_file_name + 'LZ77.txt')*100
            
    def compressW(self, data, dictionary_size, output_file):

        start_time = time.time()
        n = 256                
        maximum_table_size = pow(2,int(n))
        data = data.replace('—', '-').replace('…', '...').replace('–', '-')\
                .replace('№', '!n').replace('’', '\'').replace('‘', '\'').replace('“', '\'')\
                .replace('”', '\'').replace('„', '\'')                     
            
        dictionary = {chr(i): i for i in range(dictionary_size)}    
        string = ""            
        compressed_data = []    
        steps = []
        for symbol in data:                     
            string_plus_symbol = string + symbol
            if string_plus_symbol in dictionary: 
                string = string_plus_symbol
            else:
                compressed_data.append(dictionary[string])
                if(len(dictionary) <= maximum_table_size):
                    dictionary[string_plus_symbol] = dictionary_size
                    dictionary_size += 1
                string = symbol
            try:
                steps.append([symbol, string, dictionary[string]])
            except:
                string = ' '
                steps.append([symbol, string, dictionary[string]])

        if string in dictionary:
            compressed_data.append(dictionary[string])
        out_file = open(output_file + ".lzw", "wb")
        for data in compressed_data:
            out_file.write(pack('>L',int(data)))        
        out_file.close()
        print(output_file)

        return os.path.getsize(output_file.replace('Compressor', '') + '.txt'), \
               os.path.getsize(output_file + '.lzw'), os.path.getsize(output_file.replace('Compressor', '') + '.txt')/\
               os.path.getsize(output_file + '.lzw'), time.time() - start_time, os.path.getsize(output_file + '.lzw')/\
               os.path.getsize(output_file.replace('Compressor', '') + '.txt')*100, steps

    def decompressW(self, input_file, dictionary_size):  

        start_time = time.time()
        compressed_data = []
        file = open(input_file, "rb")
        while True:
            rec = file.read(4)
            if len(rec) != 4:
                break
            (data, ) = unpack('>L', rec)
            compressed_data.append(data)
            compressed = compressed_data

        dictionary = dict([(x, chr(x)) for x in range(dictionary_size)])

        result = StringIO()
        w = chr(compressed.pop(0))
        result.write(w)
        for k in compressed:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionary_size:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)
            dictionary[dictionary_size] = w + entry[0]
            dictionary_size += 1

            w = entry
        write_file = open(self.output_file_name + 'LZW.txt', 'w', encoding='ANSI')
        write_file.write(result.getvalue())

        return os.path.getsize(self.output_file_name + 'LZW.txt'), \
               os.path.getsize(input_file), os.path.getsize(self.output_file_name + 'LZW.txt')/\
               os.path.getsize(input_file), time.time() - start_time, os.path.getsize(input_file)/\
               os.path.getsize(self.output_file_name + 'LZW.txt')*100

    def compress78(self, data, output_file):

        start_time = time.time()
        encoded_file = open(output_file + '.lz78', 'wb')
        text_from_file = data
        text_from_file = text_from_file.replace('1', '!a').replace('2', '!b').replace('3', '!c')\
            .replace('4', '!d').replace('5', '!e').replace('6', '!f')\
            .replace('7', '!g').replace('8', '!h').replace('9', '!i').replace('0', '!g').replace('…', '')\
            .replace('–', '-').replace('№', '!n').replace('’', '\'').replace('‘', '\'').replace('“', '\'')\
            .replace('”', '\'').replace('„', '\'').replace('«', '\'').replace('»', '\'').replace('°', '\'')
        dict_of_codes = {text_from_file[0]: '1'}
        encoded_file.write(pack('>Ic',0, bytes(text_from_file[0], 'utf-8')))
        text_from_file = text_from_file[1:]
        combination = ''
        code = 2
        result = ''
        steps = []
        for char in text_from_file:
            combination += char
            if combination not in dict_of_codes:
                dict_of_codes[combination] = str(code)
                if len(combination) == 1:
                    step = '0' + combination
                    step_num = 0
                    encoded_file.write(pack('>Ic', 0, bytes(char, 'utf-8')))
                    result += step
                else:
                    step = dict_of_codes[combination[0:-1]] + combination[-1]
                    step_num = int(dict_of_codes[combination[0:-1]])
                    encoded_file.write(pack('>Ic', step_num, bytes(char, 'utf-8')))
                    result += step
                code += 1
                combination = ''
                steps.append([char, step])
        encoded_file.close()

        return os.path.getsize(output_file.replace('Compressor', '') + '.txt'), \
               os.path.getsize(output_file + '.lz78'), os.path.getsize(output_file.replace('Compressor', '') + '.txt')/\
               os.path.getsize(output_file + '.lz78'), time.time() - start_time, os.path.getsize(output_file + '.lz78')/\
               os.path.getsize(output_file.replace('Compressor', '') + '.txt')*100, steps

    def decompress78(self, input_file):

        start_time = time.time()
        output_file = self.output_file_name
        try:
            decoded_file = open(output_file + 'LZ78.txt', 'w', encoding='utf=8')
        except:
            decoded_file = open(output_file + 'LZ78.txt', 'w')

        file = open(input_file, "rb") 
        input = file.read() 
        text_from_file = ''
        i = 0
        while i<len(input):
            (num, char) = unpack(">Ic", input[i:i+5])
            i=i+5
            text_from_file += str(num) + char.decode()
        dict_of_codes = {'0': '', '1': text_from_file[1]}
        decoded_file.write(dict_of_codes['1'])
        text_from_file = text_from_file[2:]
        combination = ''
        code = 2
        decoded_text = ''
        for char in text_from_file:
            if char in '1234567890':
                combination += char
            else:
                dict_of_codes[str(code)] = dict_of_codes[combination] + char
                decoded_text += dict_of_codes[combination] + char
                combination = ''
                code += 1
        decoded_text = decoded_text.replace('!a', '1').replace('!b', '2').replace('!c', '3')\
            .replace('!d', '4').replace('!e', '5').replace('!f', '6')\
            .replace('!g', '7').replace('!h', '8').replace('!i', '9').replace('!g', '0')
        decoded_file.write(decoded_text)
        decoded_file.close()

        return os.path.getsize(self.output_file_name + 'LZ78.txt'), \
               os.path.getsize(input_file), os.path.getsize(self.output_file_name + 'LZ78.txt')/\
               os.path.getsize(input_file), time.time() - start_time, os.path.getsize(input_file)/\
               os.path.getsize(self.output_file_name + 'LZ78.txt')*100

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    compressor = Compressor()
    compressor.show()
    sys.exit(app.exec_())
        

if __name__ == '__main__':
    main()