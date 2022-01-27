# Resources used when creating this Makefile:
# - https://opensource.com/article/18/8/what-how-makefile
# - https://swcarpentry.github.io/make-novice/08-self-doc/index.html
# - https://stackoverflow.com/questions/20763629/test-whether-a-directory-exists-inside-a-makefile


.DEFAULT_GOAL := help

GREEN=\033[0;32m
RED=\033[0;31m
RESET=\033[0m  # No Color


PROJECT_ID=dev-fivetran
REGION=us-central1

VIRTUAL_ENV_FOLDER=venv


##   Commands for interacting with GCP Cloud Functions service:
##         auth                : For authenticating into gcloud service (browser prompt)
auth:
	@echo "$(GREEN)Authenticating into gcloud service...$(RESET)"
	gcloud auth login

##         list                : Lists all Cloud Functions found inside the GCP project,
##                                 add PROJECT_ID=<gcp-project> to the end of the command to use other than default.
list:
	gcloud functions list --project=$(PROJECT_ID)


##         deploy              : Deploys specified connector to target GCP project as a gcloud function
## ------------------------------------------------------------------------------------------------------
MEMORY ?= 256MB
TIMEOUT ?= 60
ENTRYPOINT ?= main
deploy:
ifeq ($(CONNECTOR_NAME),)
	@echo "$(RED)No connector_name was provided, please re-run the command and add CONNECTOR_NAME=<connector_name> at the end of the command$(RESET)"
	@echo "Example: 'make deploy CONNECTOR_NAME=my_connector'"
	exit 1
endif

# Values used for function deploy as specified by the official Fivetran cloud function guide:
# https://fivetran.com/docs/functions/google-cloud-functions/setup-guide
	@echo "$(GREEN)Deploying connector $(CONNECTOR_NAME) as a gcloud function (updates if already exists)$(RESET)"

# gcloud functions deploy reference: https://cloud.google.com/sdk/gcloud/reference/functions/deploy
	gcloud functions deploy $(CONNECTOR_NAME) \
		--source=connectors/$(CONNECTOR_NAME) \
		--ignore-file=`pwd`/.gcloudignore \
		--project=$(PROJECT_ID) \
		--region=$(REGION) \
		--entry-point=$(ENTRYPOINT) \
		--runtime=python38 \
		--memory=$(MEMORY) \
		--timeout=$(TIMEOUT)s \
		--ingress-settings=all \
		--security-level=secure-optional \
		--trigger-http \
		--service-account=gcloud-function-executor@dev-fivetran.iam.gserviceaccount.com


##   Commands for environment management:
##         setup               : Checks virtual env already exists and creates one (run @create-python-env command)
.PHONY: setup
setup:
ifneq ($(wildcard $(VIRTUAL_ENV_FOLDER)/.),)
	@echo "'$(VIRTUAL_ENV_FOLDER)/' directory already exists. Please delete it with 'make clean' and re-run this command."
else
	@make create-python-env
endif


##         create-python-env   : Creates virtual environment and installs requirements
create-python-env:
	@echo "Creating a new virtual environment in folder '$(VIRTUAL_ENV_FOLDER)/'"
	@python3 -m venv $(VIRTUAL_ENV_FOLDER)
	@export SYSTEM_VERSION_COMPAT=1

	@venv/bin/pip install -r requirements.txt
	@venv/bin/pip install -e .
	@echo "$(RED)fivetran CLI configured! It should now be ready for use.$(RESET)"


##         clean               : Removes virtual environment folder along with all installed packages
.PHONY: clean
clean:
	@rm -rf $(VIRTUAL_ENV_FOLDER)


##         help                : Prints a list of all available commands
.PHONY: help
help: Makefile
	@echo
	@echo "Commands for assisting in custom Fivetran connector development:"
	@echo
	@sed -n 's/^##//p' $<
	@echo
