from hora import const, utils
from hora.panchanga import drik
from hora.horoscope.chart import charts, house
""" Navamsa Dasa """
sidereal_year = const.sidereal_year
"""
Birth in Sign    Ar    Ta    Ge    Cn    Le    Vi    Li    Sc    Sg    Cp    Aq    Pi
9 Years          Ar    Le    Li    Aq    Ar    Le    Li    Aq    Ar    Le    Li    Aq
                 0     4     6     10    0     4     6     10    0     4     6     10
                 Li    Ar    Sg    Aq    Le    Sg    Li    Ar    Sg    Aq    Le    Sg
                 6     0     8     10    4     8     6     0     8     10    4     8
"""
dhasa_adhipati_list = [0,4,6,10,0,4,6,10,0,4,6,10]
antardhasa_list = [6,0,8,10,4,8,6,0,8,10,4,8]
dhasa_duration = 9
def get_dhasa_antardhasa(dob,tob,place,divisional_chart_factor=9,years=1,months=1,sixty_hours=1,include_antardasa=True):
    jd_at_dob = utils.julian_day_number(dob, tob)
    planet_positions = charts.divisional_chart(jd_at_dob, place, ayanamsa_mode=const._DEFAULT_AYANAMSA_MODE, 
                                               divisional_chart_factor=divisional_chart_factor, years=years, 
                                               months=months, sixty_hours=sixty_hours)
    dhasa_seed = dhasa_adhipati_list[planet_positions[0][1][0]]
    dhasa_lords = [(dhasa_seed+h)%12 for h in range(12)]
    if dhasa_seed in const.even_signs:
        dhasa_lords = [(dhasa_seed+6-h+12)%12 for h in range(12)]
    dhasa_info = []
    start_jd = jd_at_dob
    for dhasa_lord in dhasa_lords:
        duration = dhasa_duration
        bukthi_seed = antardhasa_list[dhasa_lord]
        #print('dhasa_lord',house.rasi_names_en[dhasa_lord],'bukthi seed',house.rasi_names_en[bukthi_seed])
        bhukthis = [(bukthi_seed+h)%12 for h in range(12)]
        #print('bhukthis',bhukthis)
        if include_antardasa:
            dd = duration/12
            for bhukthi_lord in bhukthis:
                y,m,d,h = utils.jd_to_gregorian(start_jd)
                dhasa_start = '%04d-%02d-%02d' %(y,m,d) +' '+utils.to_dms(h, as_string=True)
                dhasa_info.append((dhasa_lord,bhukthi_lord,dhasa_start,dd))
                start_jd += dd * sidereal_year
        else:
            y,m,d,h = utils.jd_to_gregorian(start_jd)
            dhasa_start = '%04d-%02d-%02d' %(y,m,d) +' '+utils.to_dms(h, as_string=True)
            dhasa_info.append((dhasa_lord,bhukthis,dhasa_start,duration))
            start_jd += duration * sidereal_year
    return dhasa_info
if __name__ == "__main__":
    utils.set_language('en')
    dob = (1996,12,7)
    #dob = (1819,5,24)
    #dob = (1944,8,20) #Indira Gandth
    tob = (10,34,0)
    #tob = (4,15,0)
    #tob = (8,11,0) #Indira Gandth
    place = drik.Place('Chennai',13.0878,80.2785,5.5)
    #place = drik.Place('',51+30/60,-0-10/60,0.0)
    #place = drik.Place('',18+58/60,72+50/60,5.5) #Indira Gandth
    include_antardasa = True
    sd = get_dhasa_antardhasa(dob, tob, place,include_antardasa=include_antardasa)
    if include_antardasa:
        for d,b,t,_ in sd:
            print(house.rasi_names_en[d],house.rasi_names_en[b],t)
    else:
        for d,b,t,_ in sd:
            print(house.rasi_names_en[d],b,t)
