import pytesseract
import cv2
from tkinter import *
import re 
from tkinter import ttk
import winsound
import csv
from PIL import Image, ImageTk 
#import pyodbc
from datetime import datetime
import threading



haar_cascade_path = r'F:/Pogromist/dip/CarPlate/haar_cascades/haarcascade_russian_plate_number.xml'

pytesseract.pytesseract.tesseract_cmd = r'F:/Soft/TESSERACT/tesseract.exe'
csv_file = 'data.csv'
#connection_string = 'Driver={SQL Server Native Client 11.0}; Server=(LocalDB)\MSSQLLocalDB; Database=EntryManageDB ; Trusted_Connection=yes;'
entry_address = 'ул. Московская 72а'
tesseract_config = ['--psm 6 --oem 3 -c tessedit_char_whitelist=ABCEHKMOPTXY0123456789','--psm 11 --oem 3 -c tessedit_char_whitelist=ABCEHKMOPTXY0123456789', '--psm 12 --oem 3 -c tessedit_char_whitelist=ABCEHKMOPTXY0123456789', '--psm 13 --oem 3 -c tessedit_char_whitelist=ABCEHKMOPTXY0123456789']


def open_add_car_window():
    add_car_window = Tk()
    add_car_window.title("Add car")
    add_car_window.geometry("400x200")

    label_plate = ttk.Label(add_car_window, text="Plate:")
    label_plate.grid(row=1, column=1, ipadx=6, ipady=6, padx=4, pady=4) 

    label_manufacter = ttk.Label(add_car_window, text="Manufacturer:")
    label_manufacter.grid(row=2, column=1, ipadx=6, ipady=6, padx=4, pady=4)

    label_model = ttk.Label(add_car_window, text="Model:")
    label_model.grid(row=3, column=1, ipadx=6, ipady=6, padx=4, pady=4)

    entry_plate = ttk.Entry(add_car_window)
    entry_plate.grid(row=1, column=2, ipadx=6, ipady=6, padx=4, pady=4)

    entry_manufacturer = ttk.Entry(add_car_window)
    entry_manufacturer.grid(row=2, column=2, ipadx=6, ipady=6, padx=4, pady=4)

    entry_model = ttk.Entry(add_car_window)
    entry_model.grid(row=3, column=2, ipadx=6, ipady=6, padx=4, pady=4)

    #btn = ttk.Button(add_car_window, text="Add", command=lambda: push_to_db('Car', "\'"+entry_plate.get()+"\', ", "\'"+entry_manufacturer.get()+"\',", "\'"+entry_model.get()+"\'"))
    #btn.grid(row=4, column=2, ipadx=6, ipady=6, padx=4, pady=4)

    add_car_window.mainloop()
    
def push_to_csv(plate, manufacturer, model):
    new_car = [plate, manufacturer, model]
    with open(csv_file, 'a', newline="") as file:
        writer = csv.writer(file)
        writer.writerow(new_car)

def get_image(image_path):  # чтение изображения из памяти в оттенках серого
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    #cv2.imshow("chb",binary_color_image)
    #cv2.waitKey(0) 
    return image

def bicolor_image(image):   # преобразование в ЧБ 
    (thresh, binary_color_image) = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    #cv2.imshow("chb",binary_color_image)
    #cv2.waitKey(0)
    return binary_color_image

def find_plate(image):
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    haar_cascade_classifier = cv2.CascadeClassifier(haar_cascade_path)
    
    detections = haar_cascade_classifier.detectMultiScale(image_gray, scaleFactor=1.05, minNeighbors=7)
    
    # Возвращаем пустое изображение если номер не обнаружен
    cuted_image = None
    
    for (x, y, w, h) in detections:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(image, "Number plate detected", (x - 20, y - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 255), 2)
        cuted_image = image_gray[y:y + h, x:x + w]
        cuted_image = bicolor_image(cuted_image)
        break  # Берем только первый обнаруженный номер

    # Если номер не найден, возвращаем пустое изображение
    if cuted_image is None:
        cuted_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cuted_image = cuted_image[0:1, 0:1]  # Минимальное изображение
        
    return cuted_image, image

def open_camera_window():
    video_capture = cv2.VideoCapture(0)

    width, height = 800, 600
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, width) 
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    window = Tk() 
    window.bind('<Escape>', lambda e: window.quit()) 
    window.title("Monitoring detecting")

    label_widget = Label(window) 
    label_widget.pack()  

    # Добавляем флаг для контроля потока OCR
    ocr_processing = {'active': False}

    def open_camera():
        _, frame = video_capture.read()

        plate_image, opencv_image = find_plate(frame)

        captured_image = Image.fromarray(opencv_image) 
        photo_image = ImageTk.PhotoImage(image=captured_image) 
        label_widget.photo_image = photo_image 
        label_widget.configure(image=photo_image)

        label_widget.after(10, open_camera)

        # Запускаем OCR только если предыдущий поток завершился
        # и если обнаружена пластина (размер изображения больше минимального)
        if not ocr_processing['active'] and plate_image.shape[0] > 20 and plate_image.shape[1] > 20:
            ocr_processing['active'] = True
            thr = threading.Thread(target=tesseract_read_wrapper, args=(plate_image, ocr_processing), daemon=True)
            thr.start()

    def tesseract_read_wrapper(image, flag):
        try:
            tesseract_read(image)
        finally:
            flag['active'] = False

    menu = Menu(window)  
    menu_item = Menu(menu, tearoff=0)
    menu_item.add_command(label='Add', command=open_add_car_window)  
    menu.add_cascade(label='Car', menu=menu_item)

    window.config(menu=menu)
    button1 = Button(window, text="Open Camera", command=open_camera) 
    button1.pack() 
    window.mainloop()

def tesseract_read(cuted_image):
    detected_list = []
    
    # Проверяем, что изображение не пустое
    if cuted_image is None or cuted_image.shape[0] < 20 or cuted_image.shape[1] < 20:
        return
    
    # Распознаем текст
    detected_text = str.strip(pytesseract.image_to_string(cuted_image, config=tesseract_config[0]))
    
    # Выводим сырой результат для отладки
    if detected_text:
        print(f"Raw OCR: '{detected_text}'")
        detected_list.append(detected_text)
        
        # Постобработка
        postprocessing(detected_list)

def postprocessing(detected_list):
    results = []
    
    for number in detected_list:
        if len(number) > 8:
            res1 = []
            res2 = []
            for i in range(len(number)-1): 
                res1.append(number[i])
                res2.append(number[i+1])
            detected_list.append("".join(res1))    
            detected_list.append("".join(res2))
    
    for number in detected_list:
        if len(number) == 8 or len(number) == 9:
            res0 = []
            for i in range(len(number)):
                char = number[i]
                # Позиции букв: 0, 4, 5 (и возможно 6 для региона)
                if i in [0, 4, 5] and char == "0":
                    char = "O"
                # Позиции цифр: 1, 2, 3, 6, 7
                elif i in [1, 2, 3, 6, 7, 8] and char == "O":
                    char = '0'
                res0.append(char)
            corrected = "".join(res0)
            if corrected not in detected_list:
                detected_list.append(corrected)
    
    print(f"All variants: {detected_list}")
    
    # Проверяем на соответствие формату российского номера
    for num in detected_list:
        if re.match(r'^[ABCEHKMOPTXY]\d{3}[ABCEHKMOPTXY]{2}\d{2,3}$', num):
            print(f"✓ VALID PLATE DETECTED: {num}")
            open_gates()
            results.append(num)
            break
        else:
            print(f"  Invalid format: {num}")
    
    return detected_list



def open_gates():
    winsound.Beep(500, 300)


                
def get_time(): 
    res =[]
    s = str(datetime.now())
    for i in range(len(s)-3): 
        res += s[i] 
    return "".join(res) 

def main():
    open_camera_window()
    
if __name__ == '__main__':
    main()