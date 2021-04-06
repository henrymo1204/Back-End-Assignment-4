# Back-End-Assignment-4

Group Members:
   - Tommy Huynh
   - Juheng Mo
   - Calvin Nguyen

Project notes:
The goal of this project is to implement a gateway to our code to allow authentication for API calls. 
Code does not allow users without a log in to access API calls available. Only after logging in, Users can access calls and view other user's 
posts.
Authentication is working as intended.


Folder Contents:
   - gateway.py
   - gateway.ini
   - timelines.py
   - users.py
   - Procfile
   - Readme.txt
   - Documentation_proj_4.pdf


Software Requirements:
   - python3 
   - bottle
   - foreman
   - sqlite
   
How to run:
   - $.bin/init.sh
   - $foreman start
   - to authenticate
   - http POST localhost:5000/authenticate/<username>/<password>
         
         -example username: test password: test

