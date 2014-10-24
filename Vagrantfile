# -*- mode: ruby -*-
# vi: set ft=ruby :

$name = "Walker Lee"
$synced_folder = {"#{ENV['HOME']}" => "/user",
                  "/Volumes/Transcend" => "/sdcard",
                 }

$script = <<SCRIPT
export HTTP_PROXY=http://doro.io:3128
echo 192.168.80.222 doro.io >> /etc/hosts

apt-get update
apt-get install -y python-software-properties apt-transport-https

sed -i 's#/archive.ubuntu.com/#/tw.archive.ubuntu.com/#' /etc/apt/sources.list
add-apt-repository -y ppa:fcwu-tw/ppa

# Add the repository to your APT sources
echo deb https://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list

# Then import the repository key
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9

apt-get update
apt-get install -y lxc lxc-docker
apt-get install -y qdk2 debhelper devscripts fish zsh
apt-get upgrade
apt-get clean

# docker
sed -i '$ a \
DOCKER_OPTS="--bip=10.0.5.1/24 -H tcp://127.0.0.1:4243 -H unix:///var/run/docker.sock"' /etc/default/docker
service docker stop
ip link set docker0 down
brctl delbr docker0
service docker start

chmod +s /usr/bin/docker
sudo -u vagrant git clone https://github.com/walkerlee/dotfiles .dotfiles
SCRIPT

#$script = <<SCRIPT
#echo 'Hi, #{$name}'
#SCRIPT

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"

  # config.vm.network "forwarded_port", guest: 80, host: 8080

  $synced_folder.each do |host, guest|
    if Dir.exists?(host)
      config.vm.synced_folder host, guest
    end
  end

  config.vm.provider "virtualbox" do |vb|
     vb.name = "qdk2"
     vb.memory = 2048
     vb.cpus = 2
  end

  config.vm.provision "shell", inline: $script, privileged: true
end
