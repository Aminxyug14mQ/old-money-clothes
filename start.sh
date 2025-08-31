#!/bin/bash
gunicorn app:app
python init_db.py 
python app.py
