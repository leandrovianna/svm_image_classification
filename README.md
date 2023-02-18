# Image Classification

Image Classification using Histogram of Gradients (HOG) and Support Vector 
Machines (SVM). This code is for learning purposes. Using HOG and SVM 
implementations from OpenCV and Python.

## Installing libraries

`requirements.txt` has the necessaries libraries. 
Run `pip install -r requirements.txt`.

## Tkinter interface to select images

```python
python src/select_images.py
```
GUI that show images at `images/undefined/` directory and moves to 
`images/positives/` or `images/negatives/`.

## Remove duplicate images

```python
python src/find_dupes.py
```

Using image average hash, move to a duplicates directory the image that are
similar to others in the `images/undefined/` directory. In this case, similar
means a Hamming distance of the hashes less than or equal to one.

## Training SVM model

- Use `src/params.py` to define the parameters for the HOG descriptor.
- With the positive class images at `images/positives/` and the negative class
images at `images/negatives/`, run `python src/training.py` to train the model.
- HOG descriptor will be saved on the file `models/hog_last_model.xml`.
- SVM model will be saved on the file `models/svm_last_model.dat`.

## Classification

- `src/classifier.py` run the classifier using `models/hog_model.xml` for the
HOG descriptor and `models/svm_model.dat` for SVM model.
- Input expected is a text file with an image file path on each line.
- If `visual` variable is `True`, the images will be saved on the directory
`results/` with a text indicating the classification result.

