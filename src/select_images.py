import numpy as np

import pathlib
import os
import tkinter
from tkinter.constants import BOTH, EW, TOP, BOTTOM
from PIL import ImageTk, Image


class ImageSelector:

    def __init__(self, positives_dir, negatives_dir):
        self.positives_dir = positives_dir
        self.negatives_dir = negatives_dir
        self.undefined_directory = None
        self.tk = None
        self.big_image_label = None
        self.small_image_label = None
        self.brightness_label = None
        self.images = None
        self.current = None
        self.journal = None

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

        positive_button = tkinter.Button(controls_frame,
                                         text="Positive",
                                         background='green',
                                         foreground='white',
                                         activebackground='dark green',
                                         activeforeground='white',
                                         font=50,
                                         command=lambda: self.move_image(True))
        positive_button.pack(fill=BOTH, side=TOP)
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
        skip_button = tkinter.Button(controls_frame,
                                     text="Skip",
                                     font=50,
                                     command=lambda: self.skip(1))
        skip_button.pack(fill=BOTH)
        skip_more_button = tkinter.Button(controls_frame,
                                          text="Skip 10",
                                          font=50,
                                          command=lambda: self.skip(10))
        skip_more_button.pack(fill=BOTH)
        undo_button = tkinter.Button(controls_frame,
                                     text="Undo",
                                     font=50,
                                     command=lambda: self.undo())
        undo_button.pack(fill=BOTH)

    def next_image(self):
        self.current += 1
        while self.current < len(self.images) and not os.path.isfile(
                self.images[self.current]):
            self.journal.append(('not_found', None))
            self.current += 1

        if self.current == len(self.images):
            self.close()

    def update_ui(self):
        current_image = self.images[self.current]
        filename = os.path.basename(current_image)
        self.tk.title(f'{filename} ({self.current+1}/{len(self.images)})')

        image = Image.open(current_image)

        self.big_image_label.image = ImageTk.PhotoImage(
            self.image_resize(image, 640))
        self.big_image_label.configure(image=self.big_image_label.image)
        self.small_image_label.image = ImageTk.PhotoImage(
            self.image_resize(image, 120))
        self.small_image_label.configure(image=self.small_image_label.image)
        self.brightness_label.configure(
            text=f'{filename} ({self.current+1}/{len(self.images)}) - ' +
            f'Brightness Level: {self.image_brightness(image):.02f}%')

    def move_image(self, is_positive):
        current_image = self.images[self.current]
        directory = self.positives_dir if is_positive else self.negatives_dir
        dest_img_path = os.path.join(directory,
                                     os.path.basename(current_image))
        if os.path.exists(dest_img_path):
            print('{os.path.basename(current_image)} already ' +
                  f'exists at {directory} directory.')
            self.journal.append(('skip', 1))
        else:
            os.rename(current_image, dest_img_path)
            self.journal.append(('move', dest_img_path))

        self.next_image()
        self.update_ui()

    def skip(self, count):
        self.journal.append(('skip', count))
        while count > 0:
            self.next_image()
            count -= 1
        self.update_ui()

    def undo(self):
        if len(self.journal) > 0:
            operation, param = self.journal.pop()
            if operation == 'skip':
                self.current -= param
            elif operation == 'move':
                os.rename(
                    param,
                    os.path.join(self.undefined_directory,
                                 os.path.basename(param)))
                self.current -= 1
            elif operation == 'not_found':
                self.current -= 1
                return self.undo()
            elif operation == 'begin':
                return self.close()

            self.update_ui()

    def close(self):
        self.tk.destroy()

    def select(self, directory):
        self.undefined_directory = directory
        imgs_dir = pathlib.Path(directory)
        image_files = [
            str(p) for p in imgs_dir.iterdir() if p.is_file() and (
                str(p).endswith('.jpg') or str(p).endswith('.png'))
        ]
        image_files.sort()

        self.images = image_files
        self.current = -1
        self.journal = [('begin', None)]

        self.create_widgets()
        self.next_image()
        self.update_ui()
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
