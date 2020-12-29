# SimBA - Simulation Browser and Analysis Tool for managing simulation results

## Installation
1. Clone the repository

         git clone https://github.com/solidsuccs/simba.git

2. Install using `pip3` 

         pip3 install -e /path/to/simba
         
   If you do not have `pip3` installed you san use `python3 -m pip` instead.
   
3. Test the installation by running the command

         simba

## Running SimBA Web on a remote server via SSH port forwarding

1. ssh into the remote server using the port forwarding option:

         ssh -L 1234:localhost:5678 username@server.name.edu
         
   The numbers 1234 and 5678 are arbitrary, and a value of 5000
   is recommended for both.
   `username` is your username and `server.name.edu` is the name of the
   server you are connecting to.
   Note: `localhost` is NOT arbitrary.
   
2. On the server, navigate to the correct directory and type

         simba web --ip 5678
         
   The port `5678` must match the number used in the previous step.
   If you used `5000` you do not need to specify the port as that is
   the default option for simba web.

3. On your local computer, in a browser, navigate to

         localhost:1234
         
   You should see the SimBA interface. 
