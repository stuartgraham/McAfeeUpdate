<b>Prepare Windows Machine</b><br>
Install Python 3.x manually<br>
or<br>
Command - Powershell                            #requires Powershell 3+<br>
Command - Start-Process PowerShell –Verb RunAs<br>
Command - set-executionpolicy remotesigned<br>
Command - iwr https://chocolatey.org/install.ps1 -UseBasicParsing | iex<br>
Command - choco feature enable -n allowGlobalConfirmation<br>
Command - choco install vlc -y<br>
<br>
//Prepare Python environment<br>
Command - python --version                       #should respond with 'Python 3.x.x'<br>
Command - python -m pip install requests         #should respond with 'Successfully installed requests-2.x.x'<br>
Command - python -m pip install BeautifulSoup4   #should respond with 'Successfully installed BeautifulSoup4-x.x.x'<br>