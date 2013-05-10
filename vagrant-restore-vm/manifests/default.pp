package { 'mysql-server':
  ensure => present,
}

apt::source { 'dotdeb-php54':
  location   => 'http://packages.dotdeb.org',
  release    => 'squeeze-php54',
  repos      => 'all',
  key        => '89DF5277',
  key_source => 'http://www.dotdeb.org/dotdeb.gpg',
}

package { 'php5-fpm':
  ensure  => present,
  require => Apt::Source['dotdeb-php54'],
}

nginx::vhost { 'wiki.192.168.10.23.xip.io':
    root     => '/vagrant/wiki',
    index    => 'index.php',
    template => 'nginx/vhost.php.conf.erb',
}
nginx::vhost { 'wordpress.192.168.10.23.xip.io':
    root     => '/vagrant/wordpress',
    index    => 'index.php',
    template => 'nginx/vhost.php.conf.erb',
}