import numpy as np

import pathlib
import os
import tkinter
from tkinter.constants import BOTH, EW, TOP, BOTTOM, DISABLED, NORMAL
from PIL import ImageTk, Image


class ImageSelector:

    def __init__(self, positives_dir, negatives_dir):
        self.positives_dir = positives_dir
        self.negatives_dir = negatives_dir
        self.tk = None
        self.big_image_label = None
        self.small_image_label = None
        self.brightness_label = None
        self.image_iterator = None
        self.current_image = None
        self.n_images = 0
        self.skip_count = 0
        self.control_buttons = None

    def create_widgets(self):
        self.tk = tkinter.Tk()
        self.tk.protocol('WM_DELETE_WINDOW', self.close)
        self.tk.wm_attributes('-zoomed', 1)
        self.tk.bind_all('<g>', lambda _: self.move_image(True))
        self.tk.bind_all('<b>', lambda _: self.move_image(False))
        self.tk.bind_all('<s>', lambda _: self.skip(1))
        self.tk.bind_all('<S>', lambda _: self.skip(10))
        self.tk.bind_all('<q>', lambda _: self.close())

        main_frame = tkinter.Frame(self.tk, borderwidth=2)
        main_frame.pack(fill=BOTH)

        self.big_image_label = tkinter.Label(main_frame)
        self.big_image_label.grid(column=0, row=0, rowspan=2)

        self.small_image_label = tkinter.Label(main_frame)
        self.small_image_label.grid(column=1, row=0)

        self.brightness_label = tkinter.Label(main_frame, font=50)
        self.brightness_label.grid(column=0, row=2, columnspan=2)

        controls_frame = tkinter.Frame(main_frame)
        controls_frame.grid(column=1, row=1, sticky=EW)

        self.control_buttons = []

        positive_button = tkinter.Button(controls_frame,
                                         text="Positive",
                                         background='green',
                                         foreground='white',
                                         activebackground='dark green',
                                         activeforeground='white',
                                         font=50,
                                         command=lambda: self.move_image(True))
        positive_button.pack(fill=BOTH, side=TOP)
        self.control_buttons.append(positive_button)
        negative_button = tkinter.Button(
            controls_frame,
            text="Negative",
            background='red',
            foreground='white',
            activebackground='dark red',
            activeforeground='white',
            font=50,
            command=lambda: self.move_image(False))
        negative_button.pack(fill=BOTH, side=BOTTOM)
        self.control_buttons.append(negative_button)
        skip_button = tkinter.Button(controls_frame,
                                     text="Skip",
                                     font=50,
                                     command=lambda: self.skip(1))
        skip_button.pack(fill=BOTH)
        self.control_buttons.append(skip_button)
        skip_more_button = tkinter.Button(controls_frame,
                                          text="Skip 10",
                                          font=50,
                                          command=lambda: self.skip(10))
        skip_more_button.pack(fill=BOTH)
        self.control_buttons.append(skip_more_button)

    def next_image(self):
        try:
            for button in self.control_buttons:
                button.state = DISABLED

            while self.skip_count > 0:
                next(self.image_iterator)
                self.skip_count -= 1

            index, self.current_image = next(self.image_iterator)

            while not os.path.exists(self.current_image):
                index, self.current_image = next(self.image_iterator)

            filename = os.path.basename(self.current_image)
            self.tk.title(f'{filename} ({index+1}/{self.n_images})')

            image = Image.open(self.current_image)

            self.big_image_label.image = ImageTk.PhotoImage(
                self.image_resize(image, 640))
            self.big_image_label.configure(image=self.big_image_label.image)
            self.small_image_label.image = ImageTk.PhotoImage(
                self.image_resize(image, 120))
            self.small_image_label.configure(
                image=self.small_image_label.image)
            self.brightness_label.configure(
                text=f'{filename} ({index+1}/{self.n_images}) - ' +
                f'Brightness Level: {self.image_brightness(image):.02f}%')

            for button in self.control_buttons:
                button.state = NORMAL

        except StopIteration:
            self.close()

    def move_image(self, is_positive):
        directory = self.positives_dir if is_positive else self.negatives_dir
        dest_img_path = os.path.join(directory,
                                     os.path.basename(self.current_image))
        if os.path.exists(dest_img_path):
            print('{os.path.basename(self.current_image)} already ' +
                  f'exists at {directory} directory.')
        else:
            os.rename(self.current_image, dest_img_path)

        self.next_image()

    def skip(self, count):
        self.skip_count = count - 1
        self.next_image()

    def close(self):
        self.tk.destroy()

    def select(self, directory):
        imgs_dir = pathlib.Path(directory)
        image_files = [
            p for p in map(str, imgs_dir.iterdir())
            if p.endswith('.jpg') or p.endswith('.png')
        ]
        image_files.sort()

        self.n_images = len(image_files)
        self.current_image = None
        self.image_iterator = zip(range(self.n_images), iter(image_files))
        self.skip_count = 0

        self.create_widgets()
        self.next_image()
        self.tk.mainloop()

    def image_brightness(self, image):
        gray_image = image.convert('L')
        value = np.mean(gray_image.getdata())
        return value * 100 / 255

    def image_resize(self, image, height):
        zoom = height / image.size[1]
        return image.resize(tuple(round(x * zoom) for x in image.size))


if __name__ == '__main__':
    selector = ImageSelector('images/positives', 'images/negatives')
    selector.select('images/undefined')
