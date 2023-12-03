# Interactive Dashboard for the Life Cycle Analysis of a Microwave
This app is a demo of an interactive dashboard to compute the life cycle analysis of a microwave. :link:[Link to the app.](https://life-cycle-analysis-microwave.streamlit.app/)

You can play with the different parameters to see how they impact the overall impact of the microwave. 
For instance:   
- Try changing the country of use from France to China. You will see that the 
        overall impact decreases by 13% but that the CO2 emissions are multiplied by 5!   
- Try changing the main transportation mean from boat to truck. You will see that it 
        has barely any impact!

This analyzes **4 phases**: 🛠️ Material, 🏭 Processing, 🚚 Transport, 🏠 Use-Phase and computes **3 impacts**: ☁️ climate change impact, ☢️ ionising radiations, and 🪨 depletion of abiotic resources. :link:[More info.](https://ecochain.com/blog/impact-categories-lca/).


*Made in collaboration with :link:[Holis](https://holis.earth/) 🌟*

# Installation
run `pip install -r requirements.txt`

To run the dshboard, open a terminal and run: `streamlit run main.py`
