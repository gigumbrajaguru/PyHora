from hora import const, utils
from hora.panchanga import drik
from hora.horoscope.chart import charts, house
""" Maha dasa and antardasa are OK but dhasa periods do not match with JHora """
sidereal_year = const.sidereal_year

def get_dhasa_antardhasa(dob,tob,place,divisional_chart_factor=1,years=1,months=1,sixty_hours=1,include_antardasa=True):
    jd_at_dob = utils.julian_day_number(dob, tob)
    planet_positions = charts.divisional_chart(jd_at_dob, place, ayanamsa_mode=const._DEFAULT_AYANAMSA_MODE, 
                                               divisional_chart_factor=divisional_chart_factor, years=years, 
                                               months=months, sixty_hours=sixty_hours)
    lagna = planet_positions[0][1][0]
    time_of_birth_in_hours = tob[0]+tob[1]/60+tob[2]/3600
    hora_lagna,_ = drik.hora_lagna(jd_at_dob,place,time_of_birth_in_hours,divisional_chart_factor=1)
    varnada_lagna,_ = charts.varnada_lagna(dob, tob, place)
    #print('lagna',lagna,'hora_lagna',hora_lagna,'varnada_lagna',varnada_lagna)
    dhasa_seed = house.stronger_rasi_from_planet_positions(planet_positions, lagna, hora_lagna)
    dhasa_lords = [(dhasa_seed+h)%12 for h in range(12)]
    if dhasa_seed in const.even_signs:
        dhasa_lords = [(dhasa_seed-h+12)%12 for h in range(12)]
    dhasa_info = []
    start_jd = jd_at_dob
    for dhasa_lord in dhasa_lords:
        duration = (varnada_lagna-dhasa_lord+12)%12
        bhukthis = [(dhasa_lord+h)%12 for h in range(12)]
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
    #dob = (1964,11,16)
    #dob = (1917,11,19) #Indira Gandth
    tob = (10,34,0)
    #tob = (4,30,0)
    #tob = (23,11,0) #Indira Gandth
    place = drik.Place('Chennai',13.0878,80.2785,5.5)
    #place = drik.Place('karamadai',11.2428,76.9587,5.5)
    #place = drik.Place('',25+27/60,81+51/60,5.5) #Indira Gandth
    include_antardasa = False
    sd = get_dhasa_antardhasa(dob, tob, place,include_antardasa=include_antardasa)
    if include_antardasa:
        for d,b,t,_ in sd:
            print(house.rasi_names_en[d],house.rasi_names_en[b],t)
    else:
        for d,b,t,_ in sd:
            print(house.rasi_names_en[d],b,t)
        