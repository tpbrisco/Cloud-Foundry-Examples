#/bin/bash
#
# cf-name -- give names to cloud foundry api/org/space files.
#
# Make changing between multiple cloud-foundry namespaces much easier - assign
# names to spaces, switch rapidly between spaces.
#
# Usage:
# cf-name -- show a list of available names
# cf-name [-l] <name> -- create or switch to a name, if "-l" is specified, execute a "login"
#

function usage {
    echo "Usage: cf-name [[-l|--login] [-a|--api] [-A] [-o|--org] [-s|--space]] [-r] <name>"
}

default_domain=${CF_DOMAIN:-"gaia.jpmchase.net"}
do_login=0
target_api=''
target_org=''
target_space=''
ARGS=$(getopt -o la:A:o:s:r: --long login:,api:,org:,space:,rm:,remove: -n cf-name -- "$@")
eval set -- "$ARGS"
while true ; do
    case $1 in
	-l|--login)
	    do_login=1 ; shift ;;
	-a|--api)
	    shift; target_api="-a $1"; shift;;
	-A)
	    # abbreviated - tack on default domain
	    shift; target_api="-a http://api.apps.${1}.${default_domain}" ; shift;;
	-o|--org)
	    shift; target_org="-o ${1}" ; shift ;;
	-s|--space)
	    shift; target_space="-s ${1}" ; shift ;;
	--)
	    shift ; break ;;
	\?)
	    usage
	    exit 0 ;;
	*)
	    echo "Unknown argument: $1"
	    usage
	    exit 0 ;;
    esac
done
# remaining parameter is a name - switch to it, or create it
if [ "${1}" != "" ];
then
    CF_NAME=${1}
fi

CF_HOME_DEFAULT=~/.cf-test
CF_HOME=${CF_HOME_DEFAULT:-${CF_HOME}}
# echo "CF_HOME ${CF_HOME}"

cd ${CF_HOME}
# if no name is listed, simply show what we've got
if [ "${CF_NAME}" == "" ];
then
    ls -1 *config.json | sed -e 's/[-]*config.json//'
    exit 0
fi
# if it doesn't exist, then try to create it
if [ ! -e ${CF_NAME}-config.json ] ;
then
    # is a login requested?
    if [ ${do_login} == "1" ];
    then
	# echo "cf login ${target_api} ${target_org} ${target_space}"
	cf login ${target_api} ${target_org} ${target_space}
    fi
    cp config.json ${CF_NAME}-config.json
else
    # name does exist, simply swap over to it
    cp ${CF_NAME}-config.json config.json
fi
	
