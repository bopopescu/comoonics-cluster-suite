INSTALLDIR=install
build_rpms() {
    RPMBUILDDIR=${RPMBUILDDIR:-$(rpmbuild --showrc | grep ": _topdir" | awk '{print $3}')}
		NAME=$1
	shift
    DISTRIBUTION_NAME=$1
    shift
    SHORTDISTRO=$1
    shift
	CHANGELOG=$(awk '
BEGIN { changelogfound=0; }
/^'${NAME}'/{ changelogfound=1; next };
/^comoonics/ { changelogfound=0; next };
/^mgrep/ { changelogfound=0; next };
{
  if (changelogfound == 1) {
     print
  }
}
' < docs/CHANGELOG)

    #distribution_name=$(cat $(dirname $0)/comoonics-release)

	for file in $(find $INSTALLDIR -maxdepth 1 -type f); do
  		cp $file $(basename $file)
	done

	for file in $(find $INSTALLDIR/$NAME -maxdepth 1 -type f); do
  		cp $file $(basename $file)
	done
	
	if [ $# -eq 0 ]; then
	    PYTHONPATH=./ python setup.py $NAME -v bdist_rpm --spec-only --changelog="${CHANGELOG}" --distribution-name="$DISTRIBUTION_NAME"
	    PYTHONPATH=./ python setup.py $NAME -v bdist_rpm --source-only --changelog="${CHANGELOG}" --distribution-name="$DISTRIBUTION_NAME" --defines="LINUXDISTROSHORT=${SHORTDISTRO}"
	else
		PYTHONPATH=./ python setup.py $NAME -v bdist_rpm $@ --changelog="${CHANGELOG}" --distribution-name="$distribution_name" --defines="LINUXDISTROSHORT=${SHORTDISTRO}"
	fi
	
	for file in $(find $INSTALLDIR -maxdepth 1 -type f); do
  		rm -f $(basename $file)
	done

	for file in $(find $INSTALLDIR/$NAME -maxdepth 1 -type f); do
  		rm -f $(basename $file)
	done
	rpm -ivh dist/${NAME}*.src.rpm
	cp dist/${NAME}*.src.rpm ${RPMBUILDDIR}/SRPMS/
}