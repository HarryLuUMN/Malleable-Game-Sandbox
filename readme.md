# Intro

A sandbox game that integrates a runtime behavior generation mechanism allowing dynamic mechanism evolutions in real time. 

# Launch Guide

## How to use the server and the web interface for Malleable Game Sandbox? 

- Download the word-embedding model `GoogleNews-vectors-negative300.bin` here: https://www.kaggle.com/datasets/leadbest/googlenewsvectorsnegative300 , and add the bin file into the `mgs-server` folder root.
- Create a `.env` file in the folder root, add `OPENAI_API_KEY=your_openai_key` into the `.env` file. 
- Run `python3 server.py` to launch the server. 
- Open file `index.html` to start the front-end interface, mainly for navigation and experimentation. 

## How to use the Godot game interface? 

- Started the `server.py`.
- Open the Godot project in the Godot Editor, and click run. 
