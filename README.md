# life-cycle-analysis-dashboard
This app is a demo of an interactive dashboard to compute the life cycle analysis of a microwave. 
You can play with the different parameters to see how they impact the overall impact of the microwave. 
For instance:   
- Try changing the :blue[country of use from France to China]. You will see that the 
        :green[overall impact decreases by 13%], but that the :red[CO2 emissions are multiplied by 5]!   
- Try changing the :blue[main transportation mean from boat to truck]. You will see that it 
        has barely any impact!

This app computes 3 impacts: :cloud: climate change impact, :radioactive_sign: ionising radiations, and :rock: depletion of abiotic resources. More info :link:[here](https://ecochain.com/blog/impact-categories-lca/).

*:link:[Holis](https://holis.earth/) 🌟*

# Installation
run `pip install -r requirements.txt`

To run the dshboard, open a terminal and run: `streamlit run main.py`
