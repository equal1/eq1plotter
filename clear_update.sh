# DELETE AUXILIARY BACKUP FILES AND UPDATE GITHUB SPACE
# Author: Dennis Andrade-Miceli
# Last update/review: 2020.04.21

find -type f -name '*~' -exec rm {} \;
rm core.*
git pull
git add -A -f *
git commit -m "update"
git push
