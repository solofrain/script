if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi

alias gr="grep -nr --color"
alias fn="find . -name"

alias get="scp -o 'ProxyCommand ssh ssh.nsls2.bnl.gov -W %h:%p'"

alias ssb='ssh -D 8888 -Yt ssh.bnl.gov'
alias ssc='ssh -D 8888 -Yt ssh.bnl.gov ssh -Y chinook.nsls2.bnl.gov'
alias ssd='ssh -D 8888 -Yt ssh.bnl.gov ssh -Y detector.nsls2.bnl.gov'
alias sse='ssh -D 8888 -Yt ssh.bnl.gov ssh -Y eda.nsls2.bnl.gov'
