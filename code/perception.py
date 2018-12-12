import numpy as np
import cv2


def color_thresh_bool(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    return color_select

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

def rock_thresh(img):
    color_select = np.zeros_like(img[:,:,0])
    rock_thresh = (img[:,:,0] > 60) \
                & (img[:,:,1] > 60) \
                & (img[:,:,2] < 50)
    color_select[rock_thresh] = 1
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the
    # center bottom of the image.
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle)
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image

    return warped

def clean_color(grid, x_nav, y_nav, x_rock, y_rock, x_obs, y_obs):
    print("grid shape:")
    print(grid.shape)
    grid[y_obs.astype('int64'), x_obs.astype('int64'), 0] = 200
    grid[y_rock.astype('int64'), x_rock.astype('int64'), 1] = 200
    grid[y_nav.astype('int64'), x_nav.astype('int64'), 2] = 200

    navigable = grid[:, :, 2] > 150
    grid[:,:,0][navigable] = 0
    grid[:,:,1][navigable] = 0

    rock_world = grid[:, :, 1] > 150
    grid[:,:,0][rock_world] = 0
    grid[:,:,2][rock_world] = 0

    obstacles = grid[:,:,0] > 150
    grid[:,:,1][obstacles] = 0
    grid[:,:,2][obstacles] = 0

# Apply the above funct_worldions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO:
    # NOTE: camera image is coming to you in Rover.img

    # 1) Define source and destination points for perspective transform
    dst_size = 5
    bottom_offset = 6
    image = Rover.img
    xpos = Rover.pos[0]
    ypos = Rover.pos[1]
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])

    # 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)

    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed = color_thresh(warped)
    mask = perspect_transform(np.ones((image.shape[0], image.shape[1])), source, destination)
    rock_threshed = rock_thresh(warped)

    # get obstacle threshold
    obstacle_threshold = np.logical_xor(threshed, mask)

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image

    # 5) Convert map image pixel values to rover-centric coords
    xpix_nav, ypix_nav = rover_coords(threshed)
    rock_x_rover, rock_y_rover = rover_coords(rock_threshed)
    obstacle_x_rover, obstacle_y_rover = rover_coords(obstacle_threshold)
    np.set_printoptions(threshold=np.inf)
    vision_y_nav , vision_x_nav = threshed.nonzero()
    vision_y_obs, vision_x_obs = obstacle_threshold.nonzero()
    vision_y_rock, vision_x_rock = rock_threshed.nonzero()
    #print("xpix_nav")
    #print(vision_x_nav)
    #print("ypix_nav")
    #print(vision_y_nav)

    #Rover.vision_image[vision_y_nav.astype('int64'), vision_x_nav.astype('int64'), 2] = 200
    Rover.vision_image = np.zeros_like(Rover.vision_image[:,:,:])
    clean_color(Rover.vision_image, vision_x_nav, vision_y_nav, vision_x_rock, vision_y_rock, vision_x_obs, vision_y_obs)

    # 6) Convert rover-centric pixel values to world coordinates
    scale = 20
    world_size = 200
    navigable_x_world, navigable_y_world = pix_to_world(xpix_nav, ypix_nav, xpos, ypos, Rover.yaw, world_size, scale)
    rock_x_world, rock_y_world = pix_to_world(rock_x_rover, rock_y_rover, xpos, ypos, Rover.yaw, world_size, scale)
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x_rover, obstacle_y_rover, xpos, ypos, Rover.yaw, world_size, scale)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    clean_color(Rover.worldmap, navigable_x_world, navigable_y_world, rock_x_world, rock_y_world, obstacle_x_world, obstacle_y_world)

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles
    dist, angles = to_polar_coords(xpix_nav, ypix_nav)
    Rover.nav_dists = dist
    Rover.nav_angles = angles
    mean_dir = np.mean(angles)



    return Rover
