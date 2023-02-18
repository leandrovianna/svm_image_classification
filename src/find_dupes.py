import pathlib
import os

from PIL import Image
import imagehash


def get_images(directory):
    img_files = pathlib.Path(directory).iterdir()
    imgs = [
        p for p in map(str, img_files)
        if p.endswith('.jpg') or p.endswith('.png')
    ]
    imgs.sort()
    return imgs


def flip(h, i):
    bits = h.hash.flatten().copy()
    bits[i] = not bits[i]
    return imagehash.ImageHash(bits)


def hash_compare(directory, dups_dir):
    hash_bucket = {}
    for img_path in get_images(directory):
        h = imagehash.average_hash(Image.open(img_path))
        if h in hash_bucket:
            print(f'{hash_bucket[h]} and {img_path} are similar (same hash)')
            os.rename(img_path,
                      os.path.join(dups_dir, os.path.basename(img_path)))
        else:
            hash_bucket[h] = img_path

    for h in list(hash_bucket):
        for i in range(len(h)):
            h2 = flip(h, i)
            if h2 in hash_bucket and os.path.exists(hash_bucket[h2]):
                print(f'{hash_bucket[h]} and {hash_bucket[h2]} are similar' +
                      ' (Hamming distance 1)')
                os.rename(
                    hash_bucket[h2],
                    os.path.join(dups_dir, os.path.basename(hash_bucket[h2])))
        hash_bucket.pop(h)


if __name__ == '__main__':
    directory = 'images/undefined/'
    dups_dir = os.path.join(directory, 'copies')
    if not os.path.exists(dups_dir):
        os.makedirs(dups_dir)

    hash_compare(directory, dups_dir)
