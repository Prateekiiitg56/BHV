# BHV: Behavioral Health Vault

This project aims to provide a digitization approach to record the journey of recovery of people with serious mental illnesses and other social determinants. BHV (pronounced Beehive or Behave) aim to complement traditional Electronic Healthcare Records (EHRs) to store these patient-provided images (photographs and scanned drawings) with associated textual narratives provided by the patient or recorded by a social worker through an interview.

BHV is a minimal, Python-based application that enables healthcare networks to store and retrieve patient-provided images.

It provides them access to upload, view, and edit their own images and narratives.

It also has an admin level access for the system administrators to view the entire ecosystem, upload images on behalf of the users - together with the narrative, edit images on behalf of the users, and delete images or narrations on behalf of the users or as a moderation action.

The system should be secure. But the signup process should be fairly easy. Email-based signups are ok. 

Log ins should be straightforward. A simple username, password should be sufficient.

The system should avoid unnecessary bloat, to enable easy installation in healthcare networks.

The front-end should be kept minimal, to allow the entire system to be run from a single command (rather than expecting the front-end, backend, and database to be run separately).

The storage of the images could be in file system with an index to retrieve them easily. The index itself could be in a database to allow easy query.
