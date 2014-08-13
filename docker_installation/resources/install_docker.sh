#!/bin/bash
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


PACKAGE='lxc-docker'
KEY_FINGERPRINT='36A1D7869245C8950F966E92D8576A8BA88D21E9'
KEYSERVER='keyserver.ubuntu.com'
SOURCES_LIST_FILE='/etc/apt/sources.list.d/docker.list'
SOURCES_LIST_ENTRY='deb https://get.docker.io/ubuntu docker main'

_UPDATE_SOURCES_LIST__RETRIES=12
_UPDATE_SOURCES_LIST__DELAY=5
_INSTALL_PACKAGE__RETRIES=12
_INSTALL_PACKAGE__DELAY=5


# get_package_state
#
# Checks the given package's state.
#
# $1 = package name
# result = {
#   GET_PACKAGE_STATE__INSTALLED_OK
#   GET_PACKAGE_STATE__UPGRADE
#   GET_PACKAGE_STATE__NOT_INSTALLED
# }
get_package_state(){
  declare -r tmp=`tempfile`
  echo -e "\ndpkg-query -W $1"
  dpkg-query -W "$1" 1>"${tmp}" 2>&1
  declare -r r=$?
  cat "${tmp}"
  if [ $r -eq 0 ]; then
    echo -e "\napt-cache show \"$1\" | grep Version | head -n1 | awk '{print \$2}'"
    declare -r latest_version=`apt-cache show "$1" | grep Version | head -n1 | awk '{print $2}'`
    declare -r installed_version=`cat "${tmp}" | awk '{print $2}'`
    if [ x"${installed_version}" = x"${latest_version}" ]; then
      rm "${tmp}"
      return ${GET_PACKAGE_STATE__INSTALLED_OK}
    else
      rm "${tmp}"
      return ${GET_PACKAGE_STATE__UPGRADE}
    fi
  else
    rm "${tmp}"
    return ${GET_PACKAGE_STATE__NOT_INSTALLED}
  fi
}
GET_PACKAGE_STATE__INSTALLED_OK=0     # - installed, OK, up-to-date
GET_PACKAGE_STATE__UPGRADE=1          # - installed, upgrades available
GET_PACKAGE_STATE__NOT_INSTALLED=2    # - not installed

# receive_signing_key
#
# If signing key with the given fingerprint has not been imported yet
# the function receives the key from the given keyserver and stores it in apt's
# keyring.
#
# $1 = key
# $2 = keyserver
receive_signing_key(){
  echo -e "\nsudo apt-key adv --list-keys $1"
  sudo apt-key adv --list-keys "$1"
  case $? in
    0)
      echo -e "\nKey $1 already imported. Nothing to do."
      return
      ;;
    2) ;; # key import required
    *) _error;;
  esac
  echo -e "\nsudo apt-key adv --keyserver $2 --recv-keys $1"
  sudo apt-key adv --keyserver "$2" --recv-keys "$1"
  [ $? ] || _error
}

# update_sources_list
#
# Adds the given line to the given sources list file and updates the cache.
#
# $1 = line
# $2 = file
update_sources_list(){
  echo -e "\n$1 >> $2"
  echo "$1" | sudo tee -a "$2" 1>/dev/null
  [ $? ] || _error
  declare -r tmp1=`tempfile`
  declare -r tmp2=`tempfile`
  declare i=0
  while [ $i -lt ${_UPDATE_SOURCES_LIST__RETRIES} ]; do
    i=$(( $i + 1 ))
    echo -e "\nsudo apt-get update"
    sudo apt-get update 1>"${tmp1}" 2>"${tmp2}" &
    declare -r pid_1=$!
    tail -fn+0 "${tmp1}" &
    declare -r pid_2=$!
    while [ `jobs | wc -l` -eq 2 ]; do sleep 1; done
    wait ${pid_1}
    kill ${pid_2}
    if [ $? -eq 0 ]; then
      break
    else
      cat "${tmp2}"
      sleep ${_UPDATE_SOURCES_LIST__DELAY}
    fi
  done
  rm "${tmp1}" "${tmp2}"
  [ $i -ge ${_UPDATE_SOURCES_LIST__RETRIES} ] && _error
}

# install_package
#
# Install the given package.
#
# $1 = package
install_package(){
  declare -r tmp1=`tempfile`
  declare -r tmp2=`tempfile`
  declare i=0
  while [ $i -lt ${_INSTALL_PACKAGE__RETRIES} ]; do
    i=$(( $i + 1 ))
    echo -e "\nsudo apt-get --no-install-recommends --assume-yes install $1"
    sudo apt-get --no-install-recommends --assume-yes install "$1" 1>"${tmp1}" 2>"${tmp2}" &
    declare -r pid_1=$!
    tail -fn+0 "${tmp1}" &
    declare -r pid_2=$!
    while [ `jobs | wc -l` -eq 2 ]; do sleep 1; done
    wait ${pid_1}
    kill ${pid_2}
    if [ $? -eq 0 ]; then
      break
    else
      cat "${tmp2}"
      sleep ${_INSTALL_PACKAGE__DELAY}
    fi
  done
  rm "${tmp1}" "${tmp2}"
  [ $i -ge ${_INSTALL_PACKAGE__RETRIES} ] && _error
}

# _error
#
# Prints the given message and exits with the given code.
#
# $1 = message = ''
# $2 = exit code = 1
_error(){
  [ $# -ge 1 ] && echo -e "\n$1" 1>&2
  [ $# -ge 2 ] && exit $2
  exit 1
}

# _handler
#
# Signal handler. Cleans up subprocesses in a nice way.
#
_handler(){
  declare -r subprocess_pids_1=`jobs -l | awk '{print $2}' | xargs`
  if [ x"${subprocess_pids_1}" = x ]; then
    exit
  else
    echo -e "\nkill -15 ${subprocess_pids_1}"
    kill -15 ${subprocess_pids_1} 1>/dev/null 2>&1
    sleep 1
    declare -r subprocess_pids_2=`jobs -l | awk '{print $2}' | xargs`
    if [ x"${subprocess_pids_2}" != x ]; then
      echo -e "\nkill -9 ${subprocess_pids_2}"
      kill -9 ${subprocess_pids_2} 1>/dev/null 2>&1
    fi
    exit
  fi
}


trap _handler INT
trap _handler TERM

get_package_state "${PACKAGE}"
case $? in
  ${GET_PACKAGE_STATE__INSTALLED_OK})
    echo -e "\nPackage \`${PACKAGE}' already installed and up-to-date. Nothing to do."
    ;;
  ${GET_PACKAGE_STATE__UPGRADE})
    echo -e "\nThere are upgrades to the package \`${PACKAGE}'. Upgrading."
    install_package "${PACKAGE}"
    echo -e "\nSuccessfully upgraded the package \`${PACKAGE}'."
    ;;
  ${GET_PACKAGE_STATE__NOT_INSTALLED})
    echo -e "\nPackage \`${PACKAGE}' not installed. Installing."
    receive_signing_key "${KEY_FINGERPRINT}" "${KEYSERVER}"
    update_sources_list "${SOURCES_LIST_ENTRY}" "${SOURCES_LIST_FILE}"
    install_package "${PACKAGE}"
    user=`ps --no-headers -ouser -p$$`
    succ=0
    for i in {1..30}; do
      echo -e "\nsudo usermod -a -G docker ${user}"
      sudo usermod -a -G docker "${user}"
      [ $? -eq 0 ] && {
        succ=1
        break
      }
      sleep 1;
    done
    [ $succ -eq 1 ] || _error
    echo -e "\nSuccessfully finished installing the package \`${PACKAGE}'."
    ;;
  *) _error ;;
esac
exit 0
