Masterless Puppet, versioned recipes, and an ENC
------------------------------------------------

Puppet should be treated like code, and it should have a sensible release
process.  Some people keep development, staging, and production branches and
merge code between them.  I prefer the model of tagging releases, and then
pointing a node at a specific release of modules.  All dependencies should be
tagged also, so a tagged release should be immutable.  This means you have the
very desirable property of idempotent configuration logic (ie. given the same
inputs, it should produce exactly the same output today or two years from now)

Interfaces may change across releases, so every release also requires a way to
adapt the way you use puppet classes and definitions.  For this, I prefer to
use Puppet's External Node Classifier, or ENC.  I think of the relationship
between the ENC and Puppet as the ENC making an API call to the classes.  With
this in mind, good programming practice applies - functions with the same
inputs should work the same way every time.  It's for this reason I prefer not
to rely on global parameters, facts, and using external data sources during the
puppet run (eg. Stored configs, Hiera, or mcollective queries).

As this wrapper script is just an example, I've only implemented a simple
node-specific pass-through ENC.  A more complicated version would probably
include release-specific classes which are inherited, and some kind of variable
lookup mechanisms to customise it to the datacenter, etc.  However, for a node
in an untrusted environment like the cloud, it's probably better to pre-compute
the ENC output and ship it to a node by itself.

As for why this is masterless and on-demand, it's mostly because I work with
regular application deployment, and I think that when you intend to make a
change to an application it should be explicitly on a node-by-node basis, and
you should know immediately whether it succeeded or failed, and then it should
get out of the way to let the application do its work.  This is in contrast to
standard operating system configuration (ie. for mailservers etc.) which isn't
likely to change very often, or need any coordination with other systems.

While it's possible to do versioned modules using a central puppetmaster and
changing the puppet environment, I generally prefer to split the steps when it
comes to orchestration - so I can have one step to ensure that all the code for
a release is available on the node itself, and another step to do the release.

The only trick is getting the puppet recipes to the machine in the first place.
I've purposefully used the subversion-typical layout of trunk and tags to show
a version control system as a possibility.

For the purposes of this example, I assume that I store an ENC YAML file in
/etc/puppet/input.yaml, which is, except for an extra top-level key, valid
input to Puppet's ENC.  You could of course get the ENC information from
somewhere else, such as an EC2 Instance's metadata or a web service, or it can
be passed in by your orchestration scripts.

The extra top-level key in the ENC input is called 'app' and is used to lookup
the root for the app's modules, which should contain a file called
manifest.yaml manifest.yaml file can contain a modulepath key with a list of
directories as its value, and these will be appended to the modulepath in
addition to the 'app' path.  Both the 'app' value and the 'modulepath' value
are relative to the APP_MODULE_DIR.

Example::

   root@cloud001:/etc/puppet# tree modules/
   modules/
   |-- dist
   |   `-- trunk
   |       `-- platform
   |           `-- manifests
   |               `-- init.pp
   `-- foo
       |-- tags
       |   `-- r1
       |       |-- foo
       |       |   |-- files
       |       |   |-- manifests
       |       |   |   `-- init.pp
       |       |   `-- templates
       |       `-- manifest.yaml
       `-- trunk
           |-- foo
           |   |-- files
           |   |-- manifests
           |   |   `-- init.pp
           |   `-- templates
           `-- manifest.yaml
   
   16 directories, 5 files

   root@cloud001:/etc/puppet# cat input.yaml
   app: app/foo/trunk
   classes:
     foo:
     platform:

   root@cloud001:/etc/puppet# cat modules/foo/trunk/manifest.yaml 
   modulepath:
     - dist/trunk

   root@cloud001:/etc/puppet# ./localpuppet.py
   # /usr/bin/puppet apply --node_terminus exec --external_nodes /etc/puppet/enc.sh --modulepath /etc/puppet/modules/foo/trunk:/etc/puppet/modules/dist/trunk /etc/puppet/manifests/default.pp
   notice: I notify you!
   notice: /Stage[main]/Foo/Notify[I notify you!]/message: defined 'message' as 'I notify you!'
   notice: platform class
   notice: /Stage[main]/Platform/Notify[platform class]/message: defined 'message' as 'platform class'
   notice: Finished catalog run in 0.01 seconds


Similar Work
============

While I'm not a huge fan of capistrano (as I'd rather not have anyone or
anything SSH'ing into production servers), this blogpost outlines an approach
to deploying and executing standalone Puppet recipes using it:

- http://spin.atomicobject.com/2012/07/26/standalone-puppet-with-capistrano/

Another Idea
============

I can imagine a solution where Puppet recipes are compiled to .deb or .rpm
packages (along with dependencies) and are distributed via whichever package
distribution method you use along with your software (eg. yum repo in S3,
https://github.com/rmela/yum-s3-plugin).  You could then use a tool like
mcollective to trigger a call to your_version_of_localpuppet.py with the ENC
data & app release, which would first install the appropriate recipe package
before triggering a Puppet run against the supplied ENC data.  If you use
mcollective or another tool that might timeout, or otherwise background the
run, you should have the script update status and log files, which can be later
queried for success or failure.

