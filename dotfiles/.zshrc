autoload -U compinit
compinit

HISTSIZE=65535
SAVEHIST=$HISTSIZE
HISTFILE=~/.zsh_history

export LANG="en_US.UTF-8"
export EDITOR==vim
export PATH=$PATH:~/bin

Start Stop Reload Restart () {
        /etc/init.d/$1 ${0:l}
}

function _initd {
    typeset arguments file bang
    typeset specific=${service:l}
    typeset action='(st(art|op|atus)|(force-|)re(start|load)|debug_(up|down)|dump(|_stats)|add|delete|clean|list)'
    typeset -a scripts

    if zstyle -t ':completion:*:*:_initd' all-files; then
            _arguments -s '*:init script:_path_files -W /etc/init.d -g "*(*)"'
            return 0
    fi

    for file in /etc/init.d/*(*); {
            read -u0 -k2 bang < $file && [[ $bang == '#!' ]] &&
            [[ -n ${${(j:|:s:|:)${(M)${(f)"$(< $file)"}:#[[:blank:]]#(\'|)(${~action}[[:blank:]]#\|[[:blank:]]#)#${~specific}([[:blank:]]#\|[[:blank:]]#${~action})#(\'|)\)}}//[^-a-z_]} ]] &&
            scripts+=${file##*/}
    }

    _wanted script expl script compadd $scripts
}

compdef _initd Start Stop Reload Restart


alias acp='apt-cache policy'
alias acs='apt-cache search'
alias acsh='apt-cache show'
alias acsp='apt-cache showpkg'
alias afs='apt-file search'
alias afu='apt-file update'
alias agi='apt-get install'
alias agup='apt-get update'
alias agdu='apt-get dist-upgrade'
alias agbd='apt-get build-dep'
alias dl="dpkg -L"
alias ags="apt-get source"

alias find='noglob find'
alias ls='ls -A'
alias ll='ls -lisAh'
alias df='df -hl' # human readable, only local
alias du='du -sh' # human readable, summarize

if [[ ${HOST} == vm ]] {
	alias halt="echo 'Use reboot, you noob!'"
	alias poweroff="echo 'Use reboot, you noob!'"
	alias shutdown="echo 'Use reboot, you noob!'"
}

for i ({e,f,}grep); alias $i="$i --color"

local blue=$'%{\e[1;34m%}'
local red=$'%{\e[1;31m%}'
local green=$'%{\e[1;32m%}'
local cyan=$'%{\e[1;36m%}'
local reset=$'%{\e[0m%}'

local head="%B%(?..${red}%? )${red}%m ${blue}%/ "
local tail="${reset}%b "
PS1="${head}%#${tail}"
PS2="${head}%_>${tail}"
PS3="${head}?#${tail}"
PS4="+%N:%i:%_> "

zstyle ':completion:*' menu select=1