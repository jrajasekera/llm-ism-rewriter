# Queue migration

## Before upgrading

Version 2.0 stores pending jobs in the local directory. Stop the worker and copy that directory before upgrading.

## After upgrading

Version 3.0 reads the copied directory at startup. It now stores new jobs in the database. Keep the directory until the imported jobs finish.
