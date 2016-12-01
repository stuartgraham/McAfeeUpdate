//Prep Windows Machine
Install Python 3.x manually
or
Command - Powershell                            #requires Powershell 3+
Command - Start-Process PowerShell –Verb RunAs
Command - set-executionpolicy remotesigned
Command - iwr https://chocolatey.org/install.ps1 -UseBasicParsing | iex
Command - choco feature enable -n allowGlobalConfirmation
Command - choco install vlc -y

//Prepare Python environment
Command - python --version                       #should respond with 'Python 3.x.x'
Command - python -m pip install requests         #should respond with 'Successfully installed requests-2.x.x'
Command - python -m pip install BeautifulSoup4   #should respond with 'Successfully installed BeautifulSoup4-x.x.x'