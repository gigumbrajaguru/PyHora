# -*- coding: UTF-8 -*-
import re
import sys
import os
from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from _datetime import datetime,time,date
import img2pdf
import math
from hora import utils,const
from hora.panchanga import drik
from hora.horoscope import main
from hora.ui.chart_styles import EastIndianChart, WesternChart, SouthIndianChart, NorthIndianChart, SudarsanaChakraChart
from hora.horoscope.dhasa import sudharsana_chakra

_IMAGES_PATH = '../images/'
_IMAGE_ICON_PATH=_IMAGES_PATH +"lord_ganesha2.jpg"
_DATA_PATH = '../data/'
""" UI Constants """
_main_window_width = 650
_main_window_height = 630
_info_label1_height = 200
_info_label2_height = 200
_footer_label_font_height = 8
_footer_label_height = 30
_ashtaka_chart_size_factor = 0.875
available_chart_types = ['south indian','north indian','east indian','western','sudarsana_chakra']#,'Western']
available_languages = {"English":'en','Tamil':'ta','Telugu':'te','Hindi':"hi",'Kannada':'ka'}
class ChartSimple(QWidget):
    def __init__(self,chart_type='south indian', calculation_type:str='drik'):
        super().__init__()
        self._footer_title = ''
        self._image_icon_path = _IMAGE_ICON_PATH
        self.setWindowIcon(QtGui.QIcon(self._image_icon_path))
        self._language = list(available_languages.keys())[0]
        self._chart_type = chart_type
        self._calculation_type = calculation_type.lower()
        self._ayanamsa_mode = const._DEFAULT_AYANAMSA_MODE
        """ Force Surya sidhantha ayanamsa for SS calculation type"""
        if self._calculation_type == 'ss':
            print('ChartSimple:init: Forcing ayanamsa to SURYASIDDHANTA for the SURYA SIDDHANTA calculation type')
            drik.set_ayanamsa_mode('SURYASIDDHANTA')
            self._ayanamsa_mode = 'SURYASIDDHANTA'
        ' read world cities'
        self._df = utils._world_city_db_df
        self._world_cities_db = utils.world_cities_db
        ci = _index_containing_substring(available_chart_types,chart_type.lower())
        if ci >=0:
            self._chart_type = available_chart_types[ci]
        self.setFixedSize(_main_window_width,_main_window_height)
        self.setWindowTitle('')
        self._v_layout = QVBoxLayout()
        self._create_row1_ui()
        self._create_row_2_and_3_ui()
        self._create_info_ui()
        self._create_chart_ui()
        self.compute_horoscope()        
    def _create_chart_ui(self):
        h_layout = QHBoxLayout()
        if 'south' in self._chart_type.lower():
            self._table1 = SouthIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
            self._table2 = SouthIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
        elif 'east' in self._chart_type.lower():
            self._table1 = EastIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
            self._table2 = EastIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
        elif 'west' in self._chart_type.lower():
            self._table1 = WesternChart()
            self._table2 = WesternChart()
        elif 'sudar' in self._chart_type.lower():
            self._table1 = SudarsanaChakraChart(chart_size_factor=_ashtaka_chart_size_factor)
            self._table2 = SudarsanaChakraChart(chart_size_factor=_ashtaka_chart_size_factor)
        else:
            self._table1 = NorthIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
            self._table2 = NorthIndianChart(chart_size_factor=_ashtaka_chart_size_factor)
        h_layout.addWidget(self._table1)
        h_layout.addWidget(self._table2)
        self._v_layout.addLayout(h_layout)
        self.setLayout(self._v_layout)
        self._add_footer_to_chart()
        self._v_layout.addWidget(self._footer_label)
        self._table1.update()
        self._table2.update()
    def _create_row1_ui(self):
        h_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        h_layout.addWidget(name_label)
        self._name_text = QLineEdit("Today")
        self._name = self._name_text.text()
        self._name_text.setToolTip('Enter your name')
        h_layout.addWidget(self._name_text)
        place_label = QLabel("Place:")
        h_layout.addWidget(place_label)
        self._place_name = ''
        self._place_text = QLineEdit(self._place_name)
        self._world_cities_list = utils.world_cities_list
        completer = QCompleter(self._world_cities_list)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._place_text.setCompleter(completer)
        self._place_text.textChanged.connect(self._resize_place_text_size)
        self._place_text.editingFinished.connect(lambda : self._get_location(self._place_text.text()))
        self._place_text.setToolTip('Enter place of birth, country name')
        h_layout.addWidget(self._place_text)
        lat_label = QLabel("Latidude:")
        h_layout.addWidget(lat_label)
        self._lat_text = QLineEdit('')
        self._latitude = 0.0
        self._lat_text.setToolTip('Enter Latitude preferably exact at place of birth: Format: +/- xx.xxx')
        h_layout.addWidget(self._lat_text)
        long_label = QLabel("Longitude:")
        h_layout.addWidget(long_label)
        self._long_text = QLineEdit('')
        self._longitude = 0.0
        self._long_text.setToolTip('Enter Longitude preferably exact at place of birth. Format +/- xx.xxx')
        h_layout.addWidget(self._long_text)
        tz_label = QLabel("Time Zone:")
        h_layout.addWidget(tz_label)
        self._tz_text = QLineEdit('')
        self._time_zone = 0.0
        self._tz_text.setToolTip('Enter Time offset from GMT e.g. -5.5 or 4.5')
        " Initialize with default place based on IP"
        loc = utils.get_place_from_user_ip_address()
        if loc:
            self.place(loc[0])
        h_layout.addWidget(self._tz_text)
        self._v_layout.addLayout(h_layout)
    def _reset_place_text_size(self):
        pt = 'Chennai'#self._place_text.text().split(',')[0]
        f = QFont("",0)
        fm = QFontMetrics(f)
        pw = fm.boundingRect(pt).width()
        ph = fm.height()
        self._place_text.setFixedSize(pw,ph)
        self._place_text.adjustSize()
        self._place_text.selectionStart()
        self._place_text.setCursorPosition(0)
    def _resize_place_text_size(self):
        pt = self._place_text.text()
        f = QFont("",0)
        fm = QFontMetrics(f)
        pw = fm.boundingRect(pt).width()
        ph = fm.height()
        self._place_text.setFixedSize(pw,ph)
        self._place_text.adjustSize()       
    def _get_location(self,place_name):
        result = utils.get_location(place_name)
        print('RESULT',result)
        if result:
            self._place_name,self._latitude,self._longitude,self._time_zone = result
            self._place_text.setText(self._place_name)
            self._lat_text.setText(str(self._latitude))
            self._long_text.setText(str(self._longitude))
            self._tz_text.setText(str(self._time_zone))
            print(self._place_name,self._latitude,self._longitude,self._time_zone)
        else:
            msg = place_name+" could not be found in OpenStreetMap.\nTry entering latitude and longitude manually.\nOr try entering nearest big city"
            print(msg)
            QMessageBox.about(self,"City not found",msg)
            self._lat_text.setText('')
            self._long_text.setText('')
        self._reset_place_text_size()
    def _create_row_2_and_3_ui(self):
        h_layout = QHBoxLayout()
        dob_label = QLabel("Date of Birth:")
        h_layout.addWidget(dob_label)
        self._date_of_birth = ''
        self._dob_text = QLineEdit(self._date_of_birth)
        self._dob_text.setToolTip('Date of birth in the format YYYY,MM,DD\nFor BC enter negative years.\nAllowed Year Range: -13000 (BC) to 16800 (AD)')
        h_layout.addWidget(self._dob_text)
        tob_label = QLabel("Time of Birth:")
        h_layout.addWidget(tob_label)
        self._time_of_birth = ''
        self._tob_text = QLineEdit(self._time_of_birth)
        self._tob_text.setToolTip('Enter time of birth in the format HH:MM:SS if afternoon use 12+ hours')
        current_date_str,current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
        self.date_of_birth(current_date_str)
        self.time_of_birth(current_time_str)
        h_layout.addWidget(self._tob_text)
        self._chart_type_combo = QComboBox()
        self._chart_type_combo.addItems(available_chart_types)
        self._chart_type_combo.setToolTip('Choose birth chart style north, south or east indian')
        self._chart_type_combo.setCurrentText(self._chart_type)
        h_layout.addWidget(self._chart_type_combo)
        available_ayanamsa_modes = list(const.available_ayanamsa_modes.keys())
        self._ayanamsa_combo = QComboBox()
        self._ayanamsa_combo.addItems(available_ayanamsa_modes)
        self._ayanamsa_combo.setToolTip('Choose Ayanamsa mode from the list')
        #self._ayanamsa_mode = "LAHIRI"
        self._ayanamsa_value = None
        self._ayanamsa_combo.setCurrentText(self._ayanamsa_mode)
        h_layout.addWidget(self._ayanamsa_combo)
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(available_languages.keys())
        self._lang_combo.setCurrentText(self._language)
        self._lang_combo.setToolTip('Choose language for display')
        h_layout.addWidget(self._lang_combo)
        compute_button = QPushButton("Show Chart")
        compute_button.setFont(QtGui.QFont("Arial Bold",9))
        compute_button.clicked.connect(self.compute_horoscope)
        compute_button.setToolTip('Click to update the chart information based on selections made')
        h_layout.addWidget(compute_button)
        save_image_button = QPushButton("Save as PDF")
        save_image_button.setFont(QtGui.QFont("Arial Bold",8))
        save_image_button.clicked.connect(self.save_as_pdf)
        save_image_button.setToolTip('Click to save horoscope as a PDF')
        h_layout.addWidget(save_image_button)
        self._v_layout.addLayout(h_layout)
    def _create_info_ui(self):
        h_layout = QHBoxLayout()
        self._info_label1 = QLabel("Information:")
        self._info_label1.setStyleSheet("border: 1px solid black;")
        self._info_label1.setFixedHeight(_info_label1_height)
        h_layout.addWidget(self._info_label1)
        self._info_label2 = QLabel("Information:")
        self._info_label2.setStyleSheet("border: 1px solid black;")
        self._info_label2.setFixedHeight(_info_label2_height)
        h_layout.addWidget(self._info_label2)
        self._v_layout.addLayout(h_layout)                
    def _add_footer_to_chart(self):
        self._footer_label = QLabel('')
        self._footer_label.setTextFormat(Qt.TextFormat.RichText)
        self._footer_label.setText(self._footer_title)#"Copyright © Dr. Sundar Sundaresan, Open Astro Technologies, USA.")
        self._footer_label.setStyleSheet("border: 1px solid black;")
        self._footer_label.setFont(QtGui.QFont("Arial Bold",_footer_label_font_height))
        self._footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_label.setFixedHeight(_footer_label_height)
        self._footer_label.setFixedWidth(self.width())
        self._footer_label.setWordWrap(True)
        
    def _on_application_exit(self):
        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook
        QApplication.quit()
    def ayanamsa_mode(self, ayanamsa_mode, ayanamsa=None):
        """
            Set Ayanamsa mode
            @param ayanamsa_mode - Default - Lahiri
            See 'drik.available_ayanamsa_modes' for the list of available models
        """
        self._ayanamsa_mode = ayanamsa_mode
        self._ayanamsa_value = ayanamsa
        self._ayanamsa_combo.setCurrentText(ayanamsa_mode)
    def place(self,place_name):
        """
            Set the place of birth
            @param - place_name - Specify with country code. e.g. Chennai, IN
            NOTE: Uses Nominatim to get the latitude and longitude
            An error message displayed if lat/long could not be found in which case enter lat/long manually.
        """
        self._place_name = place_name
        result = self._get_location(place_name)
        if result == None:
            return
        [self._place_name,self._latitude,self._longitude,self._time_zone] = result
    def name(self,name):
        """
            Set name of the person whose horoscope is sought
            @param - Name of person
        """
        self._name = name
        self._name_text.setText(name)
    def chart_type(self,chart_type):
        """
            Set chart type of the horoscope
            @param - chart_type:
                options: 'south indian'. 'north indian'
                Default: south indian
        """
        ci = _index_containing_substring(available_chart_types,chart_type.lower())
        if ci >=0:
            self._chart_type = available_chart_types[ci]
            self._chart_type_combo.setCurrentText(chart_type.lower())
    def latitude(self,latitude):
        """
            Sets the latitude manually
            @param - latitude
        """
        self._latitude = float(latitude)
        self._lat_text.setText(latitude)
    def longitude(self,longitude):
        """
            Sets the longitude manually
            @param - longitude
        """
        self._longitude = float(longitude)
        self._long_text.setText(longitude)
    def time_zone(self,time_zone):
        """
            Sets the time zone offset manually
            @param - time_zone - time zone offset
        """
        self._time_zone = float(time_zone)
        self._tz_text.setText(time_zone)
    def date_of_birth(self, date_of_birth):
        """
            Sets the date of birth (Format:YYYY,MM,DD)
            @param - date_of_birth
        """
        self._date_of_birth = date_of_birth
        self._dob_text.setText(self._date_of_birth)
    def time_of_birth(self, time_of_birth):
        """
            Sets the time of birth (Format:HH:MM:SS)
            @param - time_of_birth
        """
        self._time_of_birth = time_of_birth
        self._tob_text.setText(self._time_of_birth)
    def language(self,language):
        """
            Sets the language for display
            @param - language
        """
        if language in available_languages:
            self._language = language
            self._lang_combo.setCurrentText(language)
    def _validate_ui(self):
        all_data_ok = self._place_text.text().strip() != '' and \
                         self._name_text.text().strip() != '' and \
                         re.match(r"[\+|\-]?\d+\.\d+\s?", self._lat_text.text().strip(),re.IGNORECASE) and \
                         re.match(r"[\+|\-]?\d+\.\d+\s?", self._long_text.text().strip(),re.IGNORECASE) and \
                         re.match(r"[\+|\-]?\d{1,4}\,\d{1,2}\,\d{1,2}", self._dob_text.text().strip(),re.IGNORECASE) and \
                         re.match(r"\d{1,2}:\d{1,2}:\d{1,2}", self._tob_text.text().strip(),re.IGNORECASE)
        return all_data_ok        
    def compute_horoscope(self):
        """
            Compute the horoscope based on details entered
            if details missing - error is displayed            
        """
        if not self._validate_ui():
            print('values are not filled properly')
            return
        self._place_name = self._place_text.text()
        self._latitude = float(self._lat_text.text())
        self._longitude = float(self._long_text.text())
        self._time_zone = float(self._tz_text.text())
        self._language = self._lang_combo.currentText()
        self._date_of_birth = self._dob_text.text()
        self._time_of_birth = self._tob_text.text()
        if self._place_name.strip() == "":
            print("Please enter a place of birth")
            return
        self._ayanamsa_mode =  self._ayanamsa_combo.currentText()
        if self._place_name.strip() == '' and abs(self._latitude) > 0.0 and abs(self._longitude) > 0.0 and abs(self._time_zone) > 0.0: 
            [self._place_name,self._latitude,self._longitude,self._time_zone] = utils.get_location_using_nominatim(self._place_name)
            self._lat_text.setText((self._latitude))
            self._long_text.setText((self._longitude))
            self._tz_text.setText((self._time_zone))
        year,month,day = self._date_of_birth.split(",")
        birth_date = drik.Date(int(year),int(month),int(day))
        self._chart_type = self._chart_type_combo.currentText()
        ' set the chart type and reset widgets'
        self._table1.deleteLater()
        self._table2.deleteLater()
        self._footer_label.deleteLater()
        self._create_chart_ui()
        print('compute horoscope ', self._ayanamsa_mode)
        if self._place_name.strip() != '' and abs(self._latitude) > 0.0 and abs(self._longitude) > 0.0 and abs(self._time_zone) > 0.0:
            self._horo= main.Horoscope(latitude=self._latitude,longitude=self._longitude,timezone_offset=self._time_zone,date_in=birth_date,birth_time=self._time_of_birth,ayanamsa_mode=self._ayanamsa_mode,ayanamsa_value=self._ayanamsa_value,calculation_type=self._calculation_type)
        else:
            self._horo= main.Horoscope(place_with_country_code=self._place_name,date_in=birth_date,birth_time=self._time_of_birth,ayanamsa_mode=self._ayanamsa_mode,ayanamsa_value=self._ayanamsa_value,calculation_type=self._calculation_type)
        self._calendar_info = self._horo.get_calendar_information(language=available_languages[self._language])
        self._calendar_key_list= self._horo._get_calendar_resource_strings(language=available_languages[self._language])
        self._horoscope_info, self._horoscope_charts, self._vimsottari_dhasa_bhukti_info = [],[],[]
        self._horoscope_info, self._horoscope_charts = self._horo.get_horoscope_information(language=available_languages[self._language])
        _place = drik.Place(self._place_name,self._latitude,self._longitude,self._time_zone)
        _dob = self._horo.Date
        _tob = self._horo.birth_time
        _place = self._horo.Place
        self._vimsottari_dhasa_bhukthi_info = self._horo._get_vimsottari_dhasa_bhukthi(_dob,_tob,_place)
        self._update_chart_ui_with_info()
    def _fill_information_label1(self,format_str):
        info_str = ''
        key = 'sunrise_str'
        sunrise_time = self._calendar_info[self._calendar_key_list[key]]
        info_str += format_str % (self._calendar_key_list[key],sunrise_time)
        key = 'sunset_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = 'nakshatra_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = 'raasi_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = 'tithi_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = 'yogam_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = 'karanam_str'
        info_str += format_str % (self._calendar_key_list[key],self._calendar_info[self._calendar_key_list[key]])
        key = self._calendar_key_list['raasi_str']+'-'+self._calendar_key_list['ascendant_str']
        value = self._horoscope_info[key]
        info_str += format_str % (self._calendar_key_list['ascendant_str'],value)
        key = self._calendar_key_list['kali_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['vikrama_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['saka_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        self._info_label1.setText(info_str)
    def _fill_information_label2(self,format_str):
        info_str = ''
        _vimsottari_dhasa_bhukti_info = self._vimsottari_dhasa_bhukthi_info
        dhasa = [k for k,_ in _vimsottari_dhasa_bhukti_info][8].split('-')[0]
        #dhasa = [k for k,_ in self._vimsottari_dhasa_bhukti_info][8].split('-')[0]
        deb = [v for _,v in _vimsottari_dhasa_bhukti_info][8]
        #deb = [v for _,v in self._vimsottari_dhasa_bhukti_info][8]
        #print('dhasa',dhasa,'deb',deb)
        dob = self._dob_text.text().replace(',','-')
        years,months,days = _dhasa_balance(dob, deb)
        value = str(years)+':'+ str(months)+':'+ str(days)
        key = dhasa + ' '+self._calendar_key_list['balance_str']
        info_str += format_str % (key,value)
        dhasa = ''
        dhasa_end_date = ''
        di = 9
        for p,(k,v) in enumerate(_vimsottari_dhasa_bhukti_info):
            # get dhasa
            if (p+1) == di:
                dhasa = k.split("-")[0]
            # Get dhasa end Date
            elif (p+1) == di+1:
                """ to account for BC Dates negative sign is introduced"""
                if len(v.split('-')) == 4:
                    _,year,month,day = v.split('-')
                    year = '-'+year
                else:
                    year,month,day = v.split('-')
                dhasa_end_date = year+'-'+month+'-'+str(int(day)-1)+ ' '+self._calendar_key_list['ends_at_str']
                info_str += format_str % (dhasa, dhasa_end_date)
                di += 9
        key = self._calendar_key_list['maasa_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['ayanamsam_str']+' ('+self._ayanamsa_mode+') '
        value = drik.get_ayanamsa_value(self._horo.julian_day)
        self._ayanamsa_value = value
        value = utils.to_dms(value,as_string=True,is_lat_long='lat').replace('N','').replace('S','')
        print("horo_chart: Ayanamsa mode",key,'set to value',value)
        info_str += format_str % (key,value)
        key = self._calendar_key_list['samvatsara_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['kali_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['vikrama_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['saka_year_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['vaaram_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        key = self._calendar_key_list['calculation_type_str']
        value = self._calendar_info[key]
        info_str += format_str % (key,value)
        self._info_label2.setText(info_str)
    def _update_chart_ui_with_info(self):
        self._footer_label.setText(self._calendar_key_list['window_footer_title'])
        self.setWindowTitle(self._calendar_key_list['window_title'])
        format_str = '%-20s%-40s\n'
        self._fill_information_label1(format_str)
        self._fill_information_label2(format_str)
        rasi_1d = self._horoscope_charts[0] #0 for raasi chart from horoscope charts array
        rasi_1d = [x[:-1] for x in rasi_1d] # remove last \n character
        #print('rasi_1d',rasi_1d)
        jd = self._horo.julian_day  # For ascendant and planetary positions, dasa buthi - use birth time
        place = drik.Place(self._place_name,float(self._latitude),float(self._longitude),float(self._time_zone))
        planet_count = len(drik.planet_list) + 1 # Inlcuding :agnam
        upagraha_count = len(const._solar_upagraha_list) + len(const._other_upagraha_list)# + 1 # +1 for upajethu title row
        special_lagna_count = len(const._special_lagna_list)
        total_row_count = planet_count + upagraha_count + special_lagna_count
        _chart_title = self._calendar_key_list['raasi_str'] + '\n' +self._date_of_birth + \
                        '\n'+self._time_of_birth + '\n' + \
                        self._place_name + '\nGMT ' + str(self._time_zone)
        if self._chart_type.lower() == 'north indian':
            _ascendant = drik.ascendant(jd,place)
            asc_house = _ascendant[0]+1
            rasi_north = rasi_1d[asc_house-1:]+rasi_1d[0:asc_house-1]
            self._table1.setData(rasi_north)
            self._table1.update()
        elif self._chart_type.lower() == 'east indian':
            rasi_2d = _convert_1d_house_data_to_2d(rasi_1d,self._chart_type)
            row,col = _get_row_col_string_match_from_2d_list(rasi_2d,self._calendar_key_list['ascendant_str'])
            self._table1._asc_house = row*self._table1.row_count+col
            self._table1.setData(rasi_2d,chart_title=_chart_title)
            self._table1.update()
        elif self._chart_type.lower() == 'western':
            i_start = special_lagna_count # Exclude special lagna information in wester charts
            i_end = i_start + planet_count
            data = []
            for (k,v) in list(self._horoscope_info.items())[i_start:i_end]:
                k1 = k.split('-')[-1]
                v1 = v.split('-')[0]
                data.append(k1+' '+v1)
            #print('rasi data',data)
            self._table1.setData(data,chart_title=_chart_title)
            self._table1.update()
        elif self._chart_type.lower() == 'sudarsana_chakra':
            i_start = special_lagna_count # Exclude special lagna information in wester charts
            i_end = i_start + planet_count
            data = []
            #print('jd, place,self._date_of_birth',jd, place,self._date_of_birth)
            chart_1d = sudharsana_chakra.sudharshana_chakra_chart(jd, place,self._date_of_birth)#, years_from_dob, divisional_chart_factor)
            #print('chart_1d',chart_1d)
            data_1d = self._convert_1d_chart_with_planet_names(chart_1d)
            #print('data_1d',data_1d)
            self._table1.setData(data_1d)
            self._table1.update()
        else: # south indian
            rasi_2d = _convert_1d_house_data_to_2d(rasi_1d)
            row,col = _get_row_col_string_match_from_2d_list(rasi_2d,self._calendar_key_list['ascendant_str'])
            self._table1._asc_house = (row,col)
            self._table1.setData(rasi_2d,chart_title=_chart_title)
            self._table1.update()
        nava_1d = self._horoscope_charts[8] # Fixed in 1.1.0
        nava_1d = [x[:-1] for x in nava_1d]
        _chart_title = self._calendar_key_list['navamsam_str'] + '\n' +self._date_of_birth + \
                        '\n'+self._time_of_birth + '\n' + \
                        self._place_name + '\nGMT ' + str(self._time_zone)
        if self._chart_type.lower() == 'north indian':
            ascendant_longitude = drik.ascendant(jd,place)[1]
            ascendant_navamsa = drik.dasavarga_from_long(ascendant_longitude,divisional_chart_factor=9)[0]
            asc_house = ascendant_navamsa+1
            nava_north = nava_1d[asc_house-1:]+nava_1d[0:asc_house-1]
            self._table2.setData(nava_north)
            self._table2.update()
        elif self._chart_type.lower() == 'east indian':
            nava_2d = _convert_1d_house_data_to_2d(nava_1d,self._chart_type)
            row,col = _get_row_col_string_match_from_2d_list(nava_2d,self._calendar_key_list['ascendant_str'])
            self._table2._asc_house = row*self._table2.row_count+col
            self._table2.setData(nava_2d,chart_title=_chart_title)
            self._table2.update()
        elif self._chart_type.lower() == 'western':
            chart_counter = 8 # navamsam chart couner
            i_start = chart_counter * total_row_count + special_lagna_count
            i_end = i_end = i_start + planet_count
            data = []
            for (k,v) in list(self._horoscope_info.items())[i_start:i_end]:
                k1 = k.split('-')[-1]
                v1 = v.split('-')[0]
                data.append(k1+' '+v1)
            self._table2.setData(data,chart_title=_chart_title)
            self._table2.update()
        elif self._chart_type.lower() == 'sudarsana_chakra':
            #print('jd, place,self._date_of_birth',jd, place,self._date_of_birth)
            chart_1d = sudharsana_chakra.sudharshana_chakra_chart(jd, place,self._date_of_birth,years_from_dob=0, divisional_chart_factor=9)
            #print('chart_1d',chart_1d)
            data_1d = self._convert_1d_chart_with_planet_names(chart_1d)
            #print('data_1d',data_1d)
            self._table2.setData(data_1d)
            self._table2.update()
        else: # south indian
            nava_2d = _convert_1d_house_data_to_2d(nava_1d)
            row,col = _get_row_col_string_match_from_2d_list(nava_2d,self._calendar_key_list['ascendant_str'])
            self._table2._asc_house = (row,col)
            self._table2.setData(nava_2d,chart_title=_chart_title)
            self._table2.update()
    def save_as_pdf(self):
        """
            Save the displayed chart as a pdf
            Choose a file from file save dialog displayed
        """
        path = QFileDialog.getSaveFileName(self, 'Choose folder and file to save as PDF file', './output', 'PDF files (*.pdf)')#)
        pdf_file = path[0]
        image_file = "./main_window.png"
        if pdf_file:
            im = self.grab()
            im.save(image_file) 
            with open(pdf_file,"wb") as f:
                f.write(img2pdf.convert(image_file))
            f.close()
        if os.path.exists(image_file):
            os.remove(image_file)
    def _convert_1d_chart_with_planet_names(self,chart_1d_list): #To be used for Sudarsana Chakra data as input
        from hora.horoscope.chart import house
        result = []
        retrograde_planets = chart_1d_list[-1]
        #print('_convert_1d_chart_with_planet_names - retrograde_planets',retrograde_planets)
        for chart_1d in chart_1d_list[:-1]:
            #print('chart_1d',chart_1d)
            res = []
            for z,pls in chart_1d:
                #print('z',z,'pls',pls)
                pl_str = ''
                tmp = pls.split('/')
                if len(tmp) == 1 and tmp[0] =='':
                    pl_str = ''
                    res.append((z,pl_str))
                    continue
                for p in tmp:
                    if p == const._ascendant_symbol:
                        pl_str += self._calendar_key_list['ascendant_short_str']+'/'#' 'Lagnam'+'/'#const._ascendant_symbol+"/"
                    else:
                        ret_str = ''
                        if int(p) in retrograde_planets:
                            #print('planet ',utils.PLANET_SHORT_NAMES[int(p)],'is retrograde',const._retrogade_symbol)
                            ret_str = const._retrogade_symbol
                        pl_str += utils.PLANET_SHORT_NAMES[int(p)]+ret_str+'/'# house.planet_list[int(p)]+'/'#const._planet_symbols[int(p)]+'/'
                pl_str = pl_str[:-1]
                #print('tmp',tmp,(z,pl_str))
                res.append((z,pl_str))
            result.append(res)
        return result
def show_horoscope(data):
    """
        Same as class method show() to display the horoscope
        @param data - last chance to pass the data to the class
    """
    app=QApplication(sys.argv)
    window=ChartSimple(data)
    window.show()
    app.exec_()

def _index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return -1

def _convert_1d_house_data_to_2d(rasi_1d,chart_type='south indian'):
    separator = '/'
    if 'south' in chart_type.lower():
        row_count = 4
        col_count = 4
        map_to_2d = [ [11,0,1,2], [10,"","",3], [9,"","",4], [8,7,6,5] ]
    elif 'east' in chart_type.lower():
        row_count = 3
        col_count = 3
        map_to_2d = [['2'+separator+'1','0','11'+separator+'10'], ['3', "",'9' ], ['4'+separator+'5','6','7'+separator+'8']]
    rasi_2d = [['X']*row_count for _ in range(col_count)]
    for p,val in enumerate(rasi_1d):
        for index, row in enumerate(map_to_2d):
            if 'south' in chart_type.lower():
                i,j = [(index, row.index(p)) for index, row in enumerate(map_to_2d) if p in row][0]
                rasi_2d[i][j] = val
            elif 'east' in chart_type.lower():
                p_index = _index_containing_substring(row,str(p))
                if p_index != -1:
                    i,j = (index, p_index)
                    if rasi_2d[i][j] != 'X':
                        if index > 0:
                            rasi_2d[i][j] += separator + val
                        else:
                            rasi_2d[i][j] = val + separator + rasi_2d[i][j]
                    else:
                        rasi_2d[i][j] = val
    for i in range(row_count):
        for j in range(col_count):
            if rasi_2d[i][j] == 'X':
                rasi_2d[i][j] = ''
    return rasi_2d
def _get_row_col_string_match_from_2d_list(list_2d,match_string):
    for row in range(len(list_2d)):
        for col in range(len(list_2d[0])):
            if match_string in list_2d[row][col]:
                return (row,col)
def _udhayadhi_nazhikai(birth_time,sunrise_time):
    """ TODO: this will not for work for BC dates due to datetime """
    def _convert_str_to_time(str_time):
        arr = str_time.split(':')
        arr[-1] = arr[-1].replace('AM','').replace('PM','')
        return time(int(arr[0]),int(arr[1]),int(arr[2]))
    birth_time = _convert_str_to_time(birth_time)
    sunrise_time =_convert_str_to_time(sunrise_time)
    days = 0
    duration = str(datetime.combine(date.min, birth_time) - datetime.combine(date.min, sunrise_time))
    hour_sign = ''
    if " day" in duration:
        duration = str(datetime.combine(date.min, sunrise_time) - datetime.combine(date.min, birth_time))
        hour_sign = '-'
    hours,minutes,seconds = duration.split(":")
    tharparai = (int(hours)+days)*9000+int(minutes)*150+int(seconds)
    naazhigai = math.floor(tharparai/3600)
    vinadigal = math.floor( (tharparai-(naazhigai*3600))/60 )
    tharparai = math.floor(tharparai - naazhigai*3600 - vinadigal*60)
    return hour_sign+str(naazhigai)+':'+str(vinadigal)+':'+str(tharparai)
def _get_date_difference(then, now = datetime.now(), interval = "default"):
    from dateutil import relativedelta
    diff = relativedelta.relativedelta(now,then)
    years = abs(diff.years)
    months = abs(diff.months)
    days = abs(diff.days)
    return [years,months,days]
def _dhasa_balance(date_of_birth,dhasa_end_date):
    d_arr = date_of_birth.split('-')
    if len(d_arr) == 4:
        _,year,month,day = d_arr
    else:
        year,month,day = d_arr
    dob = datetime(abs(int(year)),int(month),int(day))
    d_arr = dhasa_end_date.split('-')
    if len(d_arr) == 4:
        _,year,month,day = d_arr
    else:
        year,month,day = d_arr
    ded = datetime(abs(int(year)),int(month),int(day))
    duration = _get_date_difference(dob,ded)#,starting_text="Dhasa Balance:")
    return duration
if __name__ == "__main__":
    def except_hook(cls, exception, traceback):
        print('exception called')
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook
    App = QApplication(sys.argv)
    """
    chart_type = 'Sudarsana_Chakra'
    chart = ChartSimple(chart_type=chart_type, calculation_type='drik')
    chart.language('Tamil')
    chart.name('Today')
    loc = utils.get_place_from_user_ip_address()
    print('loc from IP address',loc)
    if loc:
        chart.place(loc[0])
    current_date_str,current_time_str = datetime.now().strftime('%Y,%m,%d;%H:%M:%S').split(';')
    chart.date_of_birth(current_date_str)
    chart.time_of_birth(current_time_str)
    chart.chart_type(chart_type)
    #chart.ayanamsa_mode("SIDM_USER",0.0)
    chart.compute_horoscope()
    """
    chart_type = 'South Indian'
    chart = ChartSimple(chart_type=chart_type)
    chart.language('Tamil')
    chart.name('Today')
    chart.latitude('13.0878')
    chart.longitude('80.2785')
    chart.place('Chennai')
    chart.date_of_birth('1996,12,7')
    chart.time_of_birth('10:34:00')
    chart.chart_type(chart_type)
    chart.compute_horoscope()
    chart.show()
    sys.exit(App.exec())
