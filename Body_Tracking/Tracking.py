# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Holistic Body Tracking with MediaPipe

# %%
import mediapipe as mp
import cv2

# %% [markdown]
# ## Setting up drawing utility and holistic Model

# %%
mpDraw = mp.solutions.drawing_utils
mpHolistic = mp.solutions.holistic

# %% [markdown]
# ### Webcam Feed
#
#
# - Get the capture device, `0` is usually default
# - While its open, read the feed from the cam, and render the reading with `imshow`
# - If we press `q` Close the webcam
#     - Release Cam capture, and destroy the capturing

# %%
#Cam = cv2.VideoCapture(0)
# while Cam.isOpened():
#    ret, frame = Cam.read()
#    cv2.imshow("Holistic Detection", frame)
#
#    if cv2.waitKey(10) & 0xFF == ord("q"):
#        break
#
# Cam.release()
# cv2.destroyAllWindows()

# %% [markdown]
# ## Overlaying Holistic on the Camera Feed
#
# - Initiate Model
#   - Recolour Feed with `cv2.cvtcolor`
#   - Detect with `holistic.process`


def PosingUp():
    # * Face
    faceDots = mpDraw.DrawingSpec(
        color=(255, 255, 0), thickness=1, circle_radius=1)
    faceLines = mpDraw.DrawingSpec(
        color=(255, 0, 255), thickness=2, circle_radius=1)
    mpDraw.draw_landmarks(Image, Results.face_landmarks,
                          mpHolistic.FACE_CONNECTIONS, faceDots, faceLines)

    # * Right hand
    rightDots = mpDraw.DrawingSpec(
        color=(255, 255, 0), thickness=2, circle_radius=1)
    rightLines = mpDraw.DrawingSpec(
        color=(255, 0, 255), thickness=2, circle_radius=1)
    mpDraw.draw_landmarks(Image, Results.right_hand_landmarks,
                          mpHolistic.HAND_CONNECTIONS, rightDots, rightLines)

    # * Left hand
    leftDots = mpDraw.DrawingSpec(
        color=(255, 255, 0), thickness=2, circle_radius=1)
    leftLines = mpDraw.DrawingSpec(
        color=(255, 0, 255), thickness=2, circle_radius=1)
    mpDraw.draw_landmarks(Image, Results.left_hand_landmarks,
                          mpHolistic.HAND_CONNECTIONS, leftDots, leftLines)

    # * Pose
    poseDots = mpDraw.DrawingSpec(
        color=(255, 255, 0), thickness=1, circle_radius=1)
    poseLines = mpDraw.DrawingSpec(
        color=(255, 0, 255), thickness=1, circle_radius=1)
    mpDraw.draw_landmarks(Image, Results.pose_landmarks,
                          mpHolistic.POSE_CONNECTIONS, poseDots, poseLines)


# %%
Cam = cv2.VideoCapture(0)
with mpHolistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as Holisticc:  # ? Initiate Model
    while Cam.isOpened():
        ret, frame = Cam.read()

        Image = cv2.flip(cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB), 1)  # ? Recolor Feed
        Results = Holisticc.process(Image)  # ? Process Feed
        # print(Results.pose_landmarks) Print Dot Coordinates

        # ? Recolour Back to BGR to Render
        Image = cv2.flip(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), 1)
        PosingUp()  # ? Draw Landmarks

        cv2.imshow("Raw Feed", Image)
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

Cam.release()
cv2.destroyAllWindows()


# %%


# %%

Cam.release()
cv2.destroyAllWindows()
