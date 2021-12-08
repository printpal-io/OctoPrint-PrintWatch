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
<ul>
  <li><b>API Key:</b> the secret key used to authenticate API usage. Get yours <a href="https://printpal.io/pricing/">here</a></li>
  <li><b>Stream URL:</b> the stream address of your camera</li>
  <li><b>Enable Detection System:</b> toggle PrintWatch's detection system</li>
  <li><b>Send Email on  Detection:</b> toggle email notifications sent on detection</li>
  <li><b>Email Address:</b> the email address to send notifications</li>
  <li><b>Pause Print on Detection:</b> toggle whether the print is paused on detection</li>
  <li><b>Power off Extruder on Detection:</b> toggle whether the extruder temperature is set to ambient on detection</li>
  <li><b>Detection Threshold:</b> the threshold at which detections are to be classified as defects. This can be considered the sensitivity of the detection system.</li>
  <li><b>Toggle feedback images to API:</b> toggle whether feedback images will be sent to the model training syetm to enhance it over time.</li>
</ul>
