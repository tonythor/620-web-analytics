# 620-web-analytics

Welcome to our CUNY SPS 620 Web Analytics Repo! 

```sh
/opt/homebrew/Cellar/python\@3.10/3.10.15/bin/python3.10 -m venv .venv
source ./.venv/bin/activate
pip install -r ./requirements.txt
python -m ipykernel install --user --name data620 --display-name "data620"

# Now go publish data620_assignment1.qmd to your rpubs account. 
# This sets up the rsconnect folder in this directory. 
# And you might have to install R with brew. 

./build.sh -p 1 -h # build to html
./build.sh -p 1 -a # build and push to your rpubs
```  