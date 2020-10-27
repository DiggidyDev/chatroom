# chatroom and games with friends 

## The aim 

My aim is to create a fun solution to the awfully lonely lockdown situation that we've all had to face (in case something similar happens again, hint hint). 

Hopefully it will allow us to communicate with eachother in dire times and express our shared love for gaming and making the most of our spare time - enjoying it with one another. 

## Objectives 

0.  Create a fully-functioning chatroom (hopefully with mini-games to play with friends)! 

1. Fully-functioning chatroom(s): 

    - GUI    - Friend requests (send with messages i.e. "I found you through x, and wanted to add you for y reason") 

      - Accept/deny (With messages?) 

    - Online users 

      - Nicknames (session-specific and permanent IDs) 

        - Inappropriate language detector in names 

    - Messaging 

      - Anti-spam 

      - Direct 

      - Groupchat (invite only) 

      - Gamerooms 

        - Commands  

          - Vote skip 

          - End match 

          - Kick user 

          - (UN)(Block/mute) people (and friends) 

          - Interactive commands with users 

        - GIFs (MAYBE) 

     - Anonymous sign-in: 

        - Generate temporary UUID 

        - Only allowed to join invite-only games 

        - Account required for adding friends and directly messaging 

     - Account creation: 

        - Stores Username, UUID, Password 

 

2. Games: 

    - Games: 

      - Graph traversal - Eulerian paths and cycles 

      - Tic-tac-toe - AI (hints?) 

      - Connect-4 - AI (hints?) 

      - Hangman 

    - Chatrooms for each game session 

    - Invite-only games (send codes to friends and groupchats) 

3. Server-side: 
      - Users that sent the message see `You` instead of their nickname 
      - Have a window that opens and allows you to set the port to start hosting on, (checks if it's available – using my premade scanner from github) 
      - Handle any requests, commands, fetching users (checking if online) 
      - read/write from database (encrypt and decrypt as necessary – plaintext won't suffice 

4. Client-side: 

    - Choose nickname 

    - See friends (current activity? Set status) 

    - Set current status (idle, online) 
    - Search bar 
    - Generate UUID, send to server with data on whether user is temporary/anonymous 

     

REMEMBER GDPR 
