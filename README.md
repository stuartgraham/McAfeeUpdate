Use as a scheduled task, or one off, to sync Upstream McAfee definition repository to a local file system. Include ability to retain files for defined period of time,
traverse proxies and configure source and destination directories. <br><br>
Copy <code>config.py.example</code> and rename to <code>config.py</code>


<b>Prepare Python environment</b><br>
Tested in Python 3.5 and 3.6
<code>python --version</code>                       #should respond with 'Python 3.x.x'<br>
<code>pip install -r requirements.txt</code>         #should respond with 'Successfully installed BeautifulSoup4-x.x.x requests-2.x.x'<br>
<br> 
<b>Execution</b><br>
<code>python main.py</code><br>
<br>
<b>Logging</b><br>
<code>logs/updater.log</code><br>
<br> 
<b>Known Issues</b><br>
- Only tested in Windows file system at present
