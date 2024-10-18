from fetcher import ItemDataFetcher
from time import sleep, time, strftime
from datetime import datetime

ONE_DAY = 24 * 60 * 60
TWO_HOURS = 2 * 60 * 60

start_time = time()
readable_start_time = datetime.fromtimestamp(start_time).strftime('%A, %B %d, %Y, %H:%M:%S')

with open('log_hours.log', 'a') as log_file:
    log_file.write('Hora inicio: ' + str(readable_start_time))
    log_file.write('\n')
    log_file.write('\n')   

current_time = start_time
while current_time <= start_time + ONE_DAY:
    fetcher1 = ItemDataFetcher(4133)
    fetcher1.fetch_data()
    fecha1 = fetcher1.hora_actualizacion
    sleep(2)

    fetcher2 = ItemDataFetcher(8238)
    fetcher2.fetch_data()
    fecha2 = fetcher2.hora_actualizacion
    sleep(2)

    fetcher3 = ItemDataFetcher(4010)
    fetcher3.fetch_data()
    fecha3 = fetcher3.hora_actualizacion

    readable_current_time =  datetime.fromtimestamp(current_time).strftime('%A, %B %d, %Y, %H:%M:%S')
    
    with open('log_hours.log', 'a') as log_file:
        log_file.write('Hora ejecucion: ' + str(readable_current_time)) 
        log_file.write('\n')           
        log_file.write(fecha1)
        log_file.write('\n')
        log_file.write(fecha2)
        log_file.write('\n')
        log_file.write(fecha3)
        log_file.write('\n')

    print(readable_current_time)

    sleep(TWO_HOURS)
    current_time = time()

