BX_SLCONFIG=~/.bluemix/plugins/softlayer/config.json
BX_CONFIG=~/.bluemix/config.json

bail() {
	echo $1
	echo 'You might try to run ibmcloud sl init (choose option 2)'
	exit 1
}

bailtok() {
	echo $1
	echo 'You might need to run ibmcloud iam oauth-tokens'
	exit 1
}

extract() {
	rv=$(grep $1 $BX_CONFIG | sed -e 's/.*: //' -e 's/,//')
	dq=$(echo $rv | sed -e 's:"::g')
	echo $dq
}

extractsl() {
	rv=$(grep $1 $BX_SLCONFIG | sed -e 's/.*: //' -e 's/,//')
	dq=$(echo $rv | sed -e 's:"::g')
	echo $dq
}

[ ! -f $BX_CONFIG ] && bail 'No bluemix config file'

ims_token=$(extractsl ims_token)
[ -z "$ims_token" ] && bail "No bluemix ims_token"

ims_account_id=$(extractsl ims_account_id)
[ -z "$ims_account_id" ] && bail "No bluemix ims_account_id found"

ims_user_id=$(extractsl ims_user_id)
[ -z "$ims_user_id" ] && bail "No bluemix ims_user_id found"

sl_endpoint=$(extractsl SoftlayerApiEndpoint)
[ -z "$sl_endpoint" ] && bail "No Softlayer API endpoint found"

export ims_subject='{"ims":{"token":"'"$ims_token"'","account":'"$ims_account_id"',"user":'"$ims_user_id"',"endpoint":"'"$sl_endpoint"'","username":""},"land":{}}'

bearertok=$(extract IAMToken)
[ -z "$bearertok" ] && bailtok "No bluemix IAMToken"

export iam_token=$(echo $bearertok | sed -e 's:Bearer ::')



