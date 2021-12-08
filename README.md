<p align="center">
    <br>
    <img src="https://printpal.io/wp-content/uploads/2021/11/printwatch_background_blue-cropped_maxpng.png" width="600"/>
    <br>
<p>
<p align="center">
    <a href="https://printpal.io/">
        <img alt="Documentation" src="https://img.shields.io/badge/website-online-brightgreen">
    </a>
    <a href="https://github.com/printpal-io/OctoPrint-PrintWatch/releases">
        <img alt="GitHub release" src="https://img.shields.io/badge/release-1.0.0-blue">
    </a>
    <a href="https://printpal.pythonanywhere.com/api/status">
        <img alt="API Status" src="https://img.shields.io/badge/API%20status-paused-yellow">
    </a>
</p>
<h3 align="center">
  OctoPrint-PrintWatch
</h3>
<p align="center">
  A plugin for the client-side operations of the PrintWatch API.
</p>

<p>
  PrintWatch uses Artificial Intelligence to monitor your 3D prints for any defects that begin to form. The plugin takes actions set by the user once a failure is positively detected that include:
</p>
<ul>
  <li>📧 Email Notification/SMS</li>
  <li>⏸ Pausing the print job</li>
  <li>🔥 Turning off the Extruder Heat</li>
  <li>⚙ Any other customized actions created by the user</li>
</ul>

<p>
  PrintWatch saves time and material while also giving you peace of mind that your 3D print is printing properly.
</p>

<h3>
  Setup
</h3>
<p>
    1. Open the <b>OctoPrint Web Inferface</b>
</p>
<p>
    2. Open the <b>Settings</b> using the 🔧 (wrench) icon in the top right header
</p>
<p>
    3. Open the <b>Plugin Manager</b> in the left-side selection menu
</p>
<p>
    4. Click on the <b>"+ Get More"</b> button
</p>
<p>
    5. Search for <b>PrintWatch</b>
</p>
<p>
    6. Click <b>Install</b> on the PrintWatch Plugin
</p>
<p>
  7. Restart OctoPrint once Installation is completed
</p>
<p>
  The full installation guide/quickstart can be found here: <a href="https://printpal.io/documentation/quick-start-guide/">QuickStart Guide with OctoPrint</a>
</p>
<h3>
  Configuration
</h3>
<p>
  Once you have successfully installed PrintWatch, you should configure the settings. The Settings for PrintWatch include:
</p>
<table>
  <tr>
    <td>
      <b>Setting</b>
    </td>
    <td>
      <b>Description</b>
    </td>
  </tr>
  <tr>
    <td>
      API Key
    </td>
    <td>
      The secret key used to authenticate API usage. Get yours <a href="https://printpal.io/pricing/">here</a>
    </td>
  </tr>
  <tr>
    <td>
      Stream URL
    </td>
    <td>
      The stream address of your camera
    </td>
  </tr>
  <tr>
    <td>
      Enable Detection System
    </td>
    <td>
      Toggle PrintWatch's detection system
    </td>
  </tr>
  <tr>
    <td>
      Email Address
    </td>
    <td>
      The email address to send notifications
    </td>
  </tr>
  <tr>
    <td>
      Pause Print on Detection
    </td>
    <td>
      Toggle whether the print is paused on detection
    </td>
  </tr>
  <tr>
    <td>
      Power off Extruder on Detection
    </td>
    <td>
      Toggle whether the extruder temperature is set to ambient on detection
    </td>
  </tr>
  <tr>
    <td>
      Detection Threshold
    </td>
    <td>
      The threshold at which detections are to be classified as defects. This can be considered the sensitivity of the detection system
    </td>
  </tr>
  <tr>
    <td>
      Toggle feedback images to API
    </td>
    <td>
      Toggle feedback images to API:</b> toggle whether feedback images will be sent to the model training syetm to enhance it over time
    </td>
  </tr>
</table>

<p>
    To read more on configuring your setup, see <a href="https://printpal.io/documentation/">documentation</a>.
</p>
<p>
  To configure the settings:
</p>
<p>
    1. Open the <b>OctoPrint Web Inferface</b>
</p>
<p>
    2. Open the <b>Settings</b> using the 🔧 (wrench) icon in the top right header
</p>
<p>
    3. Scroll down to the <b>Plugin Settings</b> in the left-side selection menu and select <b>'PrintWatch'</b>
</p>
<h3>
  More about PrintWatch
</h3>
<p>
  PrintWatch is an API that allows for quick and easy deployment of machine learning models, primarily for computer vision. This Plugin implementation only accesses one of the computer vision models for detecting print defects. Read the <a href="https://printpal.io/documentation/api/">API documentation</a> to learn how to create a custom implementation of the API. Below is a table of currently implemented models, with many more to come.
</p>
<table>
  <tr>
    <td style="text-align:center">
      <b>Model</b>
    </td>
    <td style="text-align:center">
      <b>size (px)</b>
    </td>
    <td style="text-align:center">
      <b>Objects</b>
    </td>
  </tr>
  <tr>
    <td>
      DefectDetector
    </td>
    <td style="text-align:center">
      N/A
    </td>
    <td style="text-align:center">
      Defects
    </td>
  </tr>
  <tr>
    <td>
      YOLOv5s
    </td>
    <td style="text-align:center">
      640
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
  <tr>
    <td>
      YOLOv5m
    </td>
    <td style="text-align:center">
      640
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
  <tr>
    <td>
      YOLOv5l
    </td>
    <td style="text-align:center">
      640
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
  <tr>
    <td>
      YOLOv5x
    </td>
    <td style="text-align:center">
      640
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
  <tr>
    <td>
      SSD MobileNet V2
    </td>
    <td style="text-align:center">
      320
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
  <tr>
    <td>
      SSD MobileNet V2 FPN
    </td>
    <td style="text-align:center">
      640
    </td>
    <td style="text-align:center">
      COCO
    </td>
  </tr>
</table>
