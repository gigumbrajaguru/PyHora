# -*- coding: UTF-8 -*-

# vimsottari.py -- routines for computing time periods of vimsottari dhasa bhukthi
#
# Copyright by Sundar Sundaresan, USA. carnaticmusicguru2015@comcast.net
# Downloaded from https://github.com/naturalstupid
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Calculates Vimshottari (=120) Dasha-bhukthi-antara-sukshma-prana
"""
import datetime
from collections import OrderedDict as Dict
import swisseph as swe
from hora import const,utils
from hora.panchanga import drik
sidereal_year = const.savana_year #const.sidereal_year  # some say 360 days, others 365.25 or 365.2563 etc
vimsottari_adhipati = lambda nak: const.vimsottari_adhipati_list[nak % (len(const.vimsottari_adhipati_list))]
### --- Vimoshatari functions
def vimsottari_next_adhipati(lord):
    """Returns next guy after `lord` in the adhipati_list"""
    current = const.vimsottari_adhipati_list.index(lord)
    next_index = (current + 1) % len(const.vimsottari_adhipati_list)
    return const.vimsottari_adhipati_list[next_index]

def vimsottari_dasha_start_date(jd,star_position_from_moon=1):
    """Returns the start date of the mahadasa which occured on or before `jd`"""
    nak, rem = drik.nakshatra_position(jd,star_position_from_moon)
    one_star = (360 / 27.)        # 27 nakshatras span 360°
    lord = vimsottari_adhipati(nak)          # ruler of current nakshatra
    period = const.vimsottari_dict[lord]       # total years of nakshatra lord
    period_elapsed = rem / one_star * period # years
    period_elapsed *= sidereal_year        # days
    start_date = jd - period_elapsed      # so many days before current day

    return [lord, start_date]

def vimsottari_mahadasa(jdut1,star_position_from_moon=1):
    """List all mahadashas and their start dates"""
    lord, start_date = vimsottari_dasha_start_date(jdut1,star_position_from_moon)
    retval = Dict()
    for i in range(9):
        retval[lord] = start_date
        start_date += const.vimsottari_dict[lord] * sidereal_year
        lord = vimsottari_next_adhipati(lord)

    return retval

def _vimsottari_bhukti(maha_lord, start_date):
    """Compute all bhuktis of given nakshatra-lord of Mahadasa
    and its start date"""
    lord = maha_lord
    retval = Dict()
    for i in range(9):
        retval[lord] = start_date
        factor = const.vimsottari_dict[lord] * const.vimsottari_dict[maha_lord] / const.human_life_span_for_vimsottari_dhasa
        start_date += factor * sidereal_year
        lord = vimsottari_next_adhipati(lord)

    return retval

# North Indian tradition: dasa-antardasa-pratyantardasa
# South Indian tradition: dasa-bhukti-antara-sukshma
def _vimsottari_antara(maha_lord, bhukti_lord, start_date):
    """Compute all antaradasas from given bhukit's start date.
    The bhukti's lord and its lord (mahadasa lord) must be given"""
    lord = bhukti_lord
    retval = Dict()
    for i in range(9):
        retval[lord] = start_date
        factor = const.vimsottari_dict[lord] * (const.vimsottari_dict[maha_lord] / const.human_life_span_for_vimsottari_dhasa)
        factor *= (const.vimsottari_dict[bhukti_lord] / const.human_life_span_for_vimsottari_dhasa)
        start_date += factor * sidereal_year
        lord = vimsottari_next_adhipati(lord)

    return retval


def _where_occurs(jd, some_dict):
    """Returns minimum key such that some_dict[key] < jd"""
    # It is assumed that the dict is sorted in ascending order
    # i.e. some_dict[i] < some_dict[j]  where i < j
    for key in reversed(some_dict.keys()):
        if some_dict[key] < jd: return key


def compute_vimsottari_antara_from(jd, mahadashas):
    """Returns antaradasha within which given `jd` falls"""
    # Find mahadasa where this JD falls
    i = _where_occurs(jd, mahadashas)
    # Compute all bhuktis of that mahadasa
    bhuktis = _vimsottari_bhukti(i, mahadashas[i])
    # Find bhukti where this JD falls
    j = _where_occurs(jd, bhuktis)
    # JD falls in i-th dasa / j-th bhukti
    # Compute all antaras of that bhukti
    antara = _vimsottari_antara(i, j, bhuktis[j])
    return (i, j, antara)

def get_vimsottari_dhasa_bhukthi(jd,place,star_position_from_moon=1):
    """
        provides Vimsottari dhasa bhukthi for a given date in julian day (includes birth time)
        @param jd: Julian day for birthdate and birth time
        @param place: Place as tuple (place name, latitude, longitude, timezone) 
        @param star_position_from_moon: 
            1 => Default - moon
            4 => Kshema Star (4th constellation from moon)
            5 => Utpanna Star (5th constellation from moon)
            8 => Adhana Star (8th constellation from moon)
        @return: a list of [dhasa_lord,bhukthi_lord,bhukthi_start]
          Example: [ [7, 5, '1915-02-09'], [7, 0, '1917-06-10'], [7, 1, '1918-02-08'],...]
    """
    # jd is julian date with birth time included
    city,lat,long,tz = place
    jdut1 = jd - tz/24
    dashas = vimsottari_mahadasa(jdut1,star_position_from_moon)
    #print('dasha lords',dashas)
    dhasa_bukthi=[]
    for i in dashas:
        #print(' ---------- ' + get_dhasa_name(i) + ' ---------- ')
        bhuktis = _vimsottari_bhukti(i, dashas[i])
        dhasa_lord = i
        for j in bhuktis:
            bhukthi_lord = j
            jd1 = bhuktis[j]
            y, m, d, h = swe.revjul(round(jd1 + tz))
            date_str = '%04d-%02d-%02d' %(y,m,d)
            bhukthi_start = date_str
            dhasa_bukthi.append([dhasa_lord,bhukthi_lord,bhukthi_start]) 
            #dhasa_bukthi[i][j] = [dhasa_lord,bhukthi_lord,bhukthi_start]
    return dhasa_bukthi

'------ main -----------'
if __name__ == "__main__":
    from hora.tests.pvr_tests import test_example
    from hora.horoscope.chart import house
    chapter = 'Chapter 16.4 '
    exercise = 'Example 50/51 ' 
    dob = (2000,4,28)
    tob = (5,50,0)
    place = ('unknown',16.+15./60,81.+12.0/60,-4.0)
    jd = utils.julian_day_number(dob, tob)
    db = get_vimsottari_dhasa_bhukthi(jd, place)
    for d,b,s in db:
        print(d,b,s)
    exit()
    for star_position,expected_dhasa_planet in [(1,2),(4,6),(5,3),(8,0)]:
        vd = get_vimsottari_dhasa_bhukthi(jd, place,star_position_from_moon=star_position)
        test_example(chapter+exercise+'Vimsottari Tests',expected_dhasa_planet,vd[0][0],house.planet_list[expected_dhasa_planet],' Maha Dhasa at birth')
        start_date = str(dob[0])+'-'+str(dob[1])+'-'+str(dob[2])
        dy,dm,dd = utils.date_diff_in_years_months_days(start_date,vd[9][2],date_format_str="%Y-%m-%d")
        print('Balance ',house.planet_list[expected_dhasa_planet],' Dhasa, At Birth, is',dy, 'Years,', dm, 'months,', dd, 'days')
