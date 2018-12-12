## Project: Search and Sample Return
### Writeup Template: You can use this file as a template for your writeup if you want to submit it as a markdown file, but feel free to use some other method and submit a pdf if you prefer.

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/rover_image.jpg
[image2]: ./calibration_images/example_grid1.jpg
[image3]: ./calibration_images/example_rock1.jpg 

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.
To enable rock recognition, I created the rock_thresh() function to filter pixels in the image that pass my threshold of "yellow".  
As for obstacle recognition, I applied the "exclusive or", or "xor" function between my warped navigable space image, and a mask. On line 21 of process_image(), I created the mask by applying the same perspective transform I used for the warped image, to an image of all ones; this way, only the pixels that are within the rovers view, and weren't considered navigable space, will be categorized as obstacle space.  
 

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 
Once I converted rover-centric pixel values to world coordinates, I populated world map, corresponding the true map of the surroundings. Since I didn't want spots on the map to be mixes of the three colors, I assigned a priority to each color, such that the presence of blue on a pixel would insure that there would be a 0 red value on the same pixel. Similarly, green in a pixel would set the red and blue values to 0, giving rocks on the map maximum priority. (This was done starting on line 50 of process_image())  
  
Finally, the world map was overlayed with the true map to produce a video of the rover's exploration.


The video is located in ~/robo_video.mp4  


### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

The `decision_step()` is made to consider the Rover's state, and incrementally update the speed and direction that it travels in. The main addition that I made was targeted at preventing the rover from getting stuck. Normally, the rover would get stuck when it reached a rock, but there still existed navigable space in its field of vision. I added a counter to the RoverState object called "stuck_counter", that would increment when the speed remained very low while the rover was moving forward. When the stuck_counter reaches a certain threshold, I added a condition to cause the rover to rotate for several frames, and get un-stuck (decision.py:54).  

The jupyter notebook portion of the project directly translated into `perception_step()`. The main stages of the perceiving the Rover's environment are to, transform the perspective of the rover's camera to a bird's-eye-view, categorize each pixel in the image as belonging to a rock, navigable space, or obstacle space, then convert to rover coordinates, and world map coordinates (using the rover's position, and yaw value). 



#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

I ran my Rover on "good" quality.  
  
In most cases, the rover's fidelity and % mapped fluctuated around 80%. Unfortunately the time spent was very inconsistent, in some cases reaching the mile-stone in a couple of minutes, and in other cases around 10 minutes. The stuck_counter state variable I mentioned above, helped make the rover more consistent in avoiding getting stuck in rocks. Another decision I made was to have interpreted navigable space to override overlapping interpreted space. I could increase the accuracy by devising a more sophisticated scheme to compare the intensity or frequency that a certain pixel is interpreted as navigable or obstacle.  
  
The main piece I would like to improve is to cut down the rover's time exploring previously visited space. Currently, the Rover makes decisions at every frame by considering the direction that appears 'most navigable'. I would like to incorporate a memory portion such that when encountering a fork in the path, where one side is visited and the other un-visited, the rover would always pick the un-visited side.

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  



