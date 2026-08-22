# The Valhalla Routing Server Setup
To run it, the Valhalla image must of been built using the dockerfile-nhvr in it's docker folder. And be an image on the local system.
May need to adjust the name in the docker compose.
The Nginx is necessary to serve the routing API over HTTP

Put the .osm.pbf file in the directory called "custom_files" in this directory.

# Credit
FULL CREDIT for all valhalla related work goes to the Valhalla team, whom this project owes deeply.
