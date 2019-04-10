#
# cf_home - a bash function to ease connectivity to cloud foundry
# APIs.
#
# If $HOME/.cf-proxy exists, it will be used for the proxy settings
# for that CF api instance
#
# If you use multiple CF deployments, this allows you to define and
# switch between those easily, avoiding constant "cf logout", "cf api",
# and other commands associated wit CF endpoints.
#
# Usage:
# "source cf_home.sh" - creates a BASH alias to manage CF api endpoints
# cf_home -m <newname>
#    make a new "cfhome" instance, copying proxy variables from ~/.cf-proxy
# cf_home -c
#    clear CF related environment variables (i.e. turn off this)
# cf_home -l
#    list defined CFHOME endpoints
# cf_home -D
#    delete a CFHOME endpoint
# cf_home -d
#    enable debugging
# cf_home -h
#    usage message
# cf_home
#    with no parameter, cf_home prints out config and "cf target" info
# 
if [[ $( basename ${#-}) = $( basename ${BASH_SOURCE} ) ]];
then
    echo     "you want to \"source\" this script"
fi

# cloud foundry specific aliases
function cf_home () {
    function usage() {
	echo '[-m <make>, -c <clear>, -l <list>, -D <del>]'
    }
    function log() {
	if [ ${do_debug} -ne 0 ];
	then
	    echo "$1"
	fi
    }

    function switch_cfhome () {
	log "switch_cfhome"
	# switch CFHOME and proxies (if applicable)
	if [ -z "$1" ];
	then
	    log "clearing CFHOME"
	    unset CF_HOME
	    CF_PROXY=$HOME/.cf/proxy.cfg
	else
	    log "setting CF_HOME to .cf-$1"
	    export CF_HOME=$HOME/.cf-"$1"
	    export CF_PROXY=$CF_HOME/proxy.cfg
	fi
	if [ -e ${CF_PROXY} ];
	then
	    log "setting $1 proxy"
	    . ${CF_PROXY}
	else
	    echo '[proxy unset]'
	    unset http_proxy
	    unset https_proxy
	fi
    }

    # main part of cf_home function
    do_create=0
    do_delete=0
    do_debug=0
    while [ $# -gt 0 ];
    do
	# process flags
	case "$1" in
	    "-m")
		# make the directory
		log "-m create flag"
		do_create=1
		shift ;;
	    "-D")
		# delete the directory
		log "-D delete flag"
		do_delete=1
		shift ;;
	    "-c")
		# clear cf_home flags
		log "-c clear variables"
		unset CF_HOME
		shift ;;
	    "-l")
		# list CF directories
		log "-l list"
		/bin/ls -1df $HOME/.cf $HOME/.cf-*
		return 0 ;;
	    "-d")
		# enable debugging messages
		do_debug=1
		log "debugging enabled"
		shift ;;
	    "-h*")
		usage
		return 0 ;;
	    "-*")
		# unknown flag
		usage
		return 1 ;;
	    *)
		break ;;
	esac
    done
    if [ -z "$1" ];
    then
	# usage-y type of thing
	echo "CF_HOME=\"$CF_HOME\""
	cf target
	usage
	return 0
    fi
    # if deleting, make sure it exists
    if [ $do_delete == 1 ] ;
    then
	rm -rf $HOME/.cf-"$1"
	echo "[$1 deleted]"
	return 0
    fi
    if [ ${do_create} == 1 ] && [ -d $HOME/.cf-"$1" ];
    then
	# just switch to it, if it already exists
	switch_cfhome "$1"
	cf target
	return 0
    fi
    if [ $do_create == 1 ] && [ ! -d $HOME/.cf-"$1" ] ;
    then
	mkdir $HOME/.cf-"$1"
	if [ -f $HOME/.cf-proxy ];
	then
	    cp $HOME/.cf-proxy $HOME/.cf-"$1"/proxy.cfg
	else
	    echo "[no default proxy specified in \$HOME/.cf_proxy]"
	fi
	switch_cfhome "$1"
	echo "[$1 created]"
	return 0
    fi
    # all flags procssed, just switch home if it exists
    if [ ! -d $HOME/.cf-"$1" ];
    then
	echo "[no cf_home for $1 -- perhaps you meant -m?]"
	return 0
    fi
    switch_cfhome "$1"
}
