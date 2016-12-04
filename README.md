<b>Prepare Windows machine</b><br>
Install Python 3.x manually with configuration of PATH variables<br>
or<br>
<code>powershell</code>                           #requires Powershell 3+<br>
<code>Start-Process PowerShell –Verb RunAs</code> <br>
<code>set-executionpolicy remotesigned</code><br>
<code>iwr https://chocolatey.org/install.ps1 -UseBasicParsing | iex</code><br>
<code>choco feature enable -n allowGlobalConfirmation</code><br>
<code>choco install python -y</code><br>
<br>
<b>Prepare Python environment</b><br>
<code>python --version</code>                       #should respond with 'Python 3.x.x'<br>
<code>python -m pip install requests</code>         #should respond with 'Successfully installed requests-2.x.x'<br>
<code>python -m pip install BeautifulSoup4</code>   #should respond with 'Successfully installed BeautifulSoup4-x.x.x'<br>
<br>
<b>Execution</b>
<code>python main.py</code>
<br>
<b>Logging</b>
<code>the.log</code>