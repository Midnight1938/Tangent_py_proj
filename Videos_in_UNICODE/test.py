#!/home/Midnight/miniconda3/envs/AiMl/bin/python

"""
Description: Turn Videos into ASCII Art Videos
As Seen On: Instructables by Tom Savoie
# ! https://www.instructables.com/Turn-Videos-Into-ASCII-Art-Videos/
"""

from encodings import utf_8
import os
from PIL import Image, ImageOps
import imgkit
from cv2 import imwrite, imread, CAP_PROP_FPS, VideoWriter, VideoWriter_fourcc, VideoCapture

global ASCII_STR
ASCII_STR = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@', '&']


def video_2_img(path):
    """Seperate video frame-by-frame and save as jpg

    Args:
        path (string): path to video

    Returns:
        fps: the video speed
        counter-1: total amount of images
    """
    os.mkdir("Images")
    video = VideoCapture(path)  # Import video
    fps = video.get(CAP_PROP_FPS)  # Save FPS data

    sucess, image = video.read()  # Save boolean True and video frame

    counter = 1
    while sucess:
        # Add image to specified folder and name according to frame rate #
        imwrite(f"Images/Img{str(counter)}.jpg", image)
        counter += 1

    return fps, (counter-1)


def get_img(image_path):
    """Flatten the Image

    Args:
        image_path (sting): path to image

    Returns:
        initial_img: Flattened Image
    """
    init_image = Image.open(image_path)
    width, height = init_image.size  # save dimensions
    # resize with larger width to that its normal when ascii
    initial_img = init_image.resize((round(width*1.05), height))
    return initial_img


def pixel_img(image, final_width=200):
    """Resize image to set ratio

    Args:
        image ([type]): working image
        final_width (image Width, optional): Width we resize it by. Defaults to 200.

    Returns:
        image: Resized image
    """
    width, height = image.size
    # Calculate corresponding height
    final_height = int((height*final_width)/width)
    image = image.resize((final_width, final_height))
    return image


def grayscale_img(image):
    """Greyscale image
    ImageOps.grayscale() is a PIL method to render an image in grey values
    """
    image_bw = ImageOps.grayscale(image)
    return image_bw


def ascii_img(bw_image, ASCII_STR):
    """Convert BnW Image into Opacity value depending on char list

    Args:
        bw_image ([type]): the BnW image
        ASCII_STR (list): the ASCII Values

    Returns:
        image list: Stock of chars for image
    """
    pixels = bw_image.getdata()  # Create list with grey RGB Values
    ascii_img_lst = []

    for pixel in pixels:
        """ascii_conv:: With a cross-multiplication we get a value between 0
        and the number of characters in the ASCII_STR list minus 1
        (because it starts counting from 0)
        corresponding to the RGB value of it.
        In this example, a black pixel will correspond to 0 and a white pixel to 8.

        append :: From this value between 0 and 8 (if the length of the string is 9)
        we will add in our ASCII characters list,
        the character corresponding to the opacity of the pixel.
        Here, black corresponds to " " and white to "&"."""
        ascii_conv = int((pixel*len(ASCII_STR))/256)
        ascii_img_lst.append(ASCII_STR[ascii_conv])

    return ascii_img_lst


def get_colour(image):
    pixels = image.getdata()  # List with RGB values of each pixel
    return pixels


def print_ascii(ascii_list, image, colour, image_pos):
    """#? Requires
    the list of the ASCII characters
    the pixelated image (to retrieve its size)
    the color list created in STEP 6
    and the position of the image in the video (to name it and to distinguish it from the others)
    """

    with open(f'HTMLImgs/Html{str(image_pos)}.html', "w", encoding='utf_8') as file:
        file.write("""
<!DOCTYPE html>
<html>
  <body style="background-color: black">
    <pre
      style="
        display: inline-block;
        border-width: 4px 6px;
        border-color: black;
        border-style: solid;
        background-color: black;
        font-size: 32px;
        font-weight: bold;
        line-height: 60%;
      "
    ></pre>
  </body>
</html>
                """)

        width, height = image.size
        counter = 0

        for j in ascii_list:
            # transform the RGB value in color list to character
            # (with the variable counter) into hex
            color_hex = '%02x%02x%02x' % colour[counter]
            counter += 1
            if (counter % width) != 0:
                # break a line when there are the correct width
                # value per line
                file.write(
                    f"<span style=\"color: #{color_hex}\">{j}</span>")
            else:
                file.write("<br />")
        file.write("""</pre></body></html>""")


def main(video_path):
    """Madgik"""
    fps, num_img = video_2_img(video_path)
    os.mkdir('HtmlImgs')
    os.mkdir('TextImgs')

    for i in range(1, num_img+1):
        image = get_img(f'Images/Img{str(i)}.jpg')
        right_size = pixel_img(image)
        bw_image = grayscale_img(right_size)
        converted_list = ascii_img(bw_image, ASCII_STR)
        colour_list = get_colour(right_size)
        print_ascii(converted_list, right_size, colour_list, i)

# imgkit module to convert the html files into images and stock them in the TextImage folder
        imgkit.from_file(f'HtmlImgs/Html{str(i)}.hmtl',
                         f'TextImg/Img{str(i)}.jpg')

    reso = Image.open('TextImgs/Image1.jpg').size
    video = VideoWriter('finalVid.mp4', VideoWriter_fourcc(
        'm', 'p', '4', 'v'), int(fps), reso)

    for j in range(1, num_img+1):
        # cv2 module to recreate the video we've been deconstructing, but with different images
        video.write(imread(f'TextImg/Image{str(j)}.jpg'))
    video.release()


if __name__ == "__main__":
    # main("SpaceVid.mp4")
    main("Car.mp4")
