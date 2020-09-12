#
# cf_home - a bash function to ease connectivity to cloud foundry
# APIs.
#
# If $CFHOME/.cf-proxy exists, it will be used for the proxy settings
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
#
# This takes advantage of the cf-cli environment variables (see: "cf help -a"),
# which is why this is a function, and not a script.
# CF_HOME is modified to switch around environments
# CF_PLUGIN_HOME is used to avoid multiple copies of plugins
# CF_COLOR may be set optionally
# CF_PROXY_CFG
# These can be set from DEF_CF_COLOR, DEF_CF_PLUGIN_HOME,
# DEF_CF_PROXY_CFG, or just use the default values
if [[ $( basename ${#-}) = $( basename ${BASH_SOURCE} ) ]];
then
    echo     "you want to \"source\" this script"
fi

# default values
CF_COLOR=${DEF_CF_COLOR:false}
CF_PLUGIN_HOME=${DEF_CF_PLUGIN_HOME:-$HOME/.cf/plugins}
# where to find the "default" proxy configuration when creating a new CF_HOME
CF_PROXY_CFG=${DEF_CF_PROXY_CFG:-$HOME/.cf/proxy.cfg}

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
	    unset CF_PROXY
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
	    [[ ! -z "$http_proxy" ]] && echo '[proxy unset]'
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
	CF_HOME=${HOME}/.cf-"$1"
	CF_PROXY=${CF_HOME}/proxy.cfg
	mkdir ${CF_HOME}
	if [ -f ${CF_PROXY_CFG} ];
	then
	    cp ${CF_PROXY_CFG} ${CF_PROXY}
	else
	    echo "[no default proxy specified in \$CF_PROXY_CFG]"
	fi
	switch_cfhome "$1"
	echo "[$1 created]"
	return 0
    fi
    # all flags processed, just switch home if it exists
    if [ ! -d "${HOME}/.cf-$1" ];
    then
	echo "[no cf_home for $1 -- perhaps you meant -m?]"
	return 0
    fi
    switch_cfhome "$1"
}
