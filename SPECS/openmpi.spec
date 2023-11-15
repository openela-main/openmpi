# Optional name suffix to use...we leave it off when compiling with gcc, but
# for other compiled versions to install side by side, it will need a
# suffix in order to keep the names from conflicting.
#global _cc_name_suffix -gcc

%global macrosdir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

%if 0%{?fedora} >= 32 || 0%{?rhel} >= 8
%bcond_with python2
%else
%bcond_without python2
%endif

%ifarch aarch64 ppc64le x86_64
%bcond_without ucx
%else
%bcond_with ucx
%endif

# ARM 32-bit is not supported by rdma
# https://bugzilla.redhat.com/show_bug.cgi?id=1780584
%ifarch %{arm}
%bcond_with rdma
%else
%bcond_without rdma
%endif

# Run autogen - needed for some patches
%bcond_without autogen

Name:           openmpi%{?_cc_name_suffix}
Version:        4.1.1
Release:        5%{?dist}
Summary:        Open Message Passing Interface
License:        BSD and MIT and Romio
URL:            http://www.open-mpi.org/

Epoch:          2

# We can't use %%{name} here because of _cc_name_suffix
Source0:        https://www.open-mpi.org/software/ompi/v4.1/downloads/openmpi-%{version}.tar.bz2
Source1:        openmpi.module.in
Source2:        openmpi.pth.py2
Source3:        openmpi.pth.py3
Source4:        macros.openmpi
Patch1:         266189935aef4fce825d0db831b4b53accc62c32.patch
Patch2:         0001-Revert-ucx-check-supported-transports-and-devices-fo.patch

BuildRequires:  gcc-c++
BuildRequires:  gcc-gfortran
BuildRequires:  make
%if %{with autogen}
BuildRequires:  libtool
BuildRequires:  perl(Data::Dumper)
BuildRequires:  perl(File::Find)
%endif
BuildRequires:  valgrind-devel
%if %{with rdma}
BuildRequires:  opensm-devel > 3.3.0
BuildRequires:  rdma-core-devel
%endif
# Doesn't compile:
# vt_dyn.cc:958:28: error: 'class BPatch_basicBlockLoop' has no member named 'getLoopHead'
#                      loop->getLoopHead()->getStartAddress(), loop_stmts );
#BuildRequires:  dyninst-devel
BuildRequires:  hwloc-devel >= 2.2.0
# So configure can find lstopo
BuildRequires:  hwloc-gui
BuildRequires:  java-devel
# Old libevent causes issues
%if !0%{?el7}
BuildRequires:  libevent-devel
%endif
BuildRequires:  libfabric-devel
%ifnarch s390 s390x
BuildRequires:  papi-devel
%endif
BuildRequires:  perl-generators
BuildRequires:  perl-interpreter
BuildRequires:  perl(Getopt::Long)
BuildRequires:  pmix-devel
BuildRequires:  python%{python3_pkgversion}-devel
%ifarch x86_64
BuildRequires:  libpsm2-devel
%endif
%if %{with ucx}
BuildRequires:  ucx-devel
%endif
BuildRequires:  zlib-devel
%if !0%{?el7}
BuildRequires:  rpm-mpi-hooks
%endif

Provides:       mpi
%if 0%{?rhel} == 7
# Need this for /etc/profile.d/modules.sh
Requires:       environment-modules
%endif
Requires:       environment(modules)
# openmpi currently requires ssh to run
# https://svn.open-mpi.org/trac/ompi/ticket/4228
Requires:       openssh-clients

# Private openmpi libraries
%global __provides_exclude_from %{_libdir}/openmpi/lib/(lib(mca|ompi|open-(pal|rte|trace))|openmpi/).*.so
%global __requires_exclude lib(mca|ompi|open-(pal|rte|trace)|vt).*

%description
Open MPI is an open source, freely available implementation of both the
MPI-1 and MPI-2 standards, combining technologies and resources from
several other projects (FT-MPI, LA-MPI, LAM/MPI, and PACX-MPI) in
order to build the best MPI library available.  A completely new MPI-2
compliant implementation, Open MPI offers advantages for system and
software vendors, application developers, and computer science
researchers. For more information, see http://www.open-mpi.org/ .

%package devel
Summary:	Development files for openmpi
Requires:	%{name} = %{epoch}:%{version}-%{release}, gcc-gfortran
Provides:	mpi-devel
%if !0%{?el7}
Requires:	rpm-mpi-hooks
# Make sure this package is rebuilt with correct Python version when updating
# Otherwise mpi.req from rpm-mpi-hooks doesn't work
# https://bugzilla.redhat.com/show_bug.cgi?id=1705296
Requires:	(python(abi) = %{python3_version} if python3)
%endif

%description devel
Contains development headers and libraries for openmpi.

%package java
Summary:        Java library
Requires:       %{name} = %{epoch}:%{version}-%{release}
Requires:       java-headless

%description java
Java library.

%package java-devel
Summary:        Java development files for openmpi
Requires:       %{name}-java = %{epoch}:%{version}-%{release}
Requires:       java-devel

%description java-devel
Contains development wrapper for compiling Java with openmpi.

# We set this to for convenience, since this is the unique dir we use for this
# particular package, version, compiler
%global namearch openmpi-%{_arch}%{?_cc_name_suffix}

%if %{with python2}
%package -n python2-openmpi
Summary:        OpenMPI support for Python 2
BuildRequires:  python2-devel
Requires:       %{name} = %{epoch}:%{version}-%{release}
Requires:       python(abi) = %{python2_version}

%description -n python2-openmpi
OpenMPI support for Python 2.
%endif

%package -n python%{python3_pkgversion}-openmpi
Summary:        OpenMPI support for Python 3
Requires:       %{name} = %{epoch}:%{version}-%{release}
Requires:       python(abi) = %{python3_version}

%description -n python%{python3_pkgversion}-openmpi
OpenMPI support for Python 3.


%prep
%autosetup -p1 -n %{name}-%{version}
%if %{with autogen}
./autogen.pl --force
%endif


%build
%set_build_flags
./configure --prefix=%{_libdir}/%{name} \
	--mandir=%{_mandir}/%{namearch} \
	--includedir=%{_includedir}/%{namearch} \
	--sysconfdir=%{_sysconfdir}/%{namearch} \
	--disable-silent-rules \
	--enable-builtin-atomics \
	--enable-mpi-cxx \
	--enable-mpi-java \
	--enable-mpi1-compatibility \
	--with-sge \
	--with-valgrind \
	--enable-memchecker \
	--with-hwloc=/usr \
%if !0%{?el7}
	--with-libevent=external \
	--with-pmix=external \
%endif

%make_build V=1

%install
%make_install
find %{buildroot}%{_libdir}/%{name}/lib -name \*.la | xargs rm
find %{buildroot}%{_mandir}/%{namearch} -type f | xargs gzip -9
ln -s mpicc.1.gz %{buildroot}%{_mandir}/%{namearch}/man1/mpiCC.1.gz
# Remove dangling symlink
rm %{buildroot}%{_mandir}/%{namearch}/man1/mpiCC.1
mkdir %{buildroot}%{_mandir}/%{namearch}/man{2,4,5,6,8,9,n}

# Make the environment-modules file
mkdir -p %{buildroot}%{_datadir}/modulefiles/mpi
# Since we're doing our own substitution here, use our own definitions.
sed 's#@LIBDIR@#%{_libdir}/%{name}#;
     s#@ETCDIR@#%{_sysconfdir}/%{namearch}#;
     s#@FMODDIR@#%{_fmoddir}/%{name}#;
     s#@INCDIR@#%{_includedir}/%{namearch}#;
     s#@MANDIR@#%{_mandir}/%{namearch}#;
%if %{with python2}
     s#@PY2SITEARCH@#%{python2_sitearch}/%{name}#;
%else
     /@PY2SITEARCH@/d;
%endif
     s#@PY3SITEARCH@#%{python3_sitearch}/%{name}#;
     s#@COMPILER@#openmpi-%{_arch}%{?_cc_name_suffix}#;
     s#@SUFFIX@#%{?_cc_name_suffix}_openmpi#' \
     <%{SOURCE1} \
     >%{buildroot}%{_datadir}/modulefiles/mpi/%{namearch}

# make the rpm config file
install -Dpm 644 %{SOURCE4} %{buildroot}/%{macrosdir}/macros.%{namearch}

# Link the fortran module to proper location
mkdir -p %{buildroot}%{_fmoddir}/%{name}
for mod in %{buildroot}%{_libdir}/%{name}/lib/*.mod
do
  modname=$(basename $mod)
  ln -s ../../../%{name}/lib/${modname} %{buildroot}/%{_fmoddir}/%{name}/
done

# Link the pkgconfig files into the main namespace as well
mkdir -p %{buildroot}%{_libdir}/pkgconfig
cd %{buildroot}%{_libdir}/pkgconfig
ln -s ../%{name}/lib/pkgconfig/*.pc .
cd -

# Remove extraneous wrapper link libraries (bug 814798)
sed -i -e s/-ldl// -e s/-lhwloc// \
  %{buildroot}%{_libdir}/%{name}/share/openmpi/*-wrapper-data.txt

# install .pth files
%if %{with python2}
mkdir -p %{buildroot}/%{python2_sitearch}/%{name}
install -pDm0644 %{SOURCE2} %{buildroot}/%{python2_sitearch}/openmpi.pth
%endif
mkdir -p %{buildroot}/%{python3_sitearch}/%{name}
install -pDm0644 %{SOURCE3} %{buildroot}/%{python3_sitearch}/openmpi.pth

%check
make check

%files
%license LICENSE
%dir %{_libdir}/%{name}
%dir %{_sysconfdir}/%{namearch}
%dir %{_libdir}/%{name}/bin
%dir %{_libdir}/%{name}/lib
%dir %{_libdir}/%{name}/lib/openmpi
%dir %{_mandir}/%{namearch}
%dir %{_mandir}/%{namearch}/man*
%config(noreplace) %{_sysconfdir}/%{namearch}/*
%{_libdir}/%{name}/bin/mpi[er]*
%{_libdir}/%{name}/bin/ompi*
%{_libdir}/%{name}/bin/orte[-dr_]*
%if %{with ucx}
%{_libdir}/%{name}/bin/oshmem_info
%{_libdir}/%{name}/bin/oshrun
%{_libdir}/%{name}/bin/shmemrun
%endif
%{_libdir}/%{name}/lib/*.so.40*
%{_libdir}/%{name}/lib/libmca_common_ofi.so.10*
%{_libdir}/%{name}/lib/libmca*.so.41*
%{_libdir}/%{name}/lib/libmca*.so.50*
%if 0%{?el7}
%{_libdir}/%{name}/lib/pmix/
%endif
%{_mandir}/%{namearch}/man1/mpi[er]*
%{_mandir}/%{namearch}/man1/ompi*
%{_mandir}/%{namearch}/man1/orte[-dr_]*
%if %{with ucx}
%{_mandir}/%{namearch}/man1/oshmem_info*
%{_mandir}/%{namearch}/man1/oshrun*
%{_mandir}/%{namearch}/man1/shmemrun*
%endif
%{_mandir}/%{namearch}/man7/ompi_*
%{_mandir}/%{namearch}/man7/opal_*
%{_mandir}/%{namearch}/man7/orte*
%{_libdir}/%{name}/lib/openmpi/*
%{_datadir}/modulefiles/mpi/
%dir %{_libdir}/%{name}/share
%dir %{_libdir}/%{name}/share/openmpi
%{_libdir}/%{name}/share/openmpi/amca-param-sets
%{_libdir}/%{name}/share/openmpi/help*.txt
%if %{with rdma}
%{_libdir}/%{name}/share/openmpi/mca-btl-openib-device-params.ini
%endif
%if 0%{?el7}
%{_libdir}/%{name}/share/pmix/
%endif

%files devel
%dir %{_includedir}/%{namearch}
%{_libdir}/%{name}/bin/aggregate_profile.pl
%{_libdir}/%{name}/bin/mpi[cCf]*
%{_libdir}/%{name}/bin/opal_*
%{_libdir}/%{name}/bin/orte[cCf]*
%if %{with ucx}
%{_libdir}/%{name}/bin/osh[cCf]*
%endif
%{_libdir}/%{name}/bin/profile2mat.pl
%if %{with ucx}
%{_libdir}/%{name}/bin/shmem[cCf]*
%endif
%{_includedir}/%{namearch}/*
%{_fmoddir}/%{name}/
%{_libdir}/%{name}/lib/*.so
%{_libdir}/%{name}/lib/*.mod
%{_libdir}/%{name}/lib/pkgconfig/
%{_libdir}/pkgconfig/*.pc
%{_mandir}/%{namearch}/man1/mpi[cCf]*
%if %{with ucx}
%{_mandir}/%{namearch}/man1/osh[cCf]*
%{_mandir}/%{namearch}/man1/shmem[cCf]*
%endif
%{_mandir}/%{namearch}/man1/opal_*
%{_mandir}/%{namearch}/man3/*
%{_libdir}/%{name}/share/openmpi/openmpi-valgrind.supp
%{_libdir}/%{name}/share/openmpi/*-wrapper-data.txt
%{macrosdir}/macros.%{namearch}

%files java
%{_libdir}/%{name}/lib/mpi.jar

%files java-devel
%{_libdir}/%{name}/bin/mpijavac
%{_libdir}/%{name}/bin/mpijavac.pl
# Currently this only contaings openmpi/javadoc
%{_libdir}/%{name}/share/doc/
%{_mandir}/%{namearch}/man1/mpijavac.1.gz

%if %{with python2}
%files -n python2-openmpi
%dir %{python2_sitearch}/%{name}
%{python2_sitearch}/openmpi.pth
%endif

%files -n python%{python3_pkgversion}-openmpi
%dir %{python3_sitearch}/%{name}
%{python3_sitearch}/openmpi.pth


%changelog
* Fri Jul 21 2023 Kamal Heib <kheib@redhat.com> - 2:4.1.1-5
- Increase Epoch tag
- Resolves: rhbz#2221806, rhbz#2159630

* Thu Jul 20 2023 Kamal Heib <kheib@redhat.com> - 1:4.1.1-4
- Bump version
- Revert v4.1.5
- Resolves: rhbz#2221806, rhbz#2159630

* Wed Feb 16 2022 Honggang Li <honli@redhat.com> - 4.1.1-3
- Revert upstream v4.1.2
- Add Epoch tag
- Related: rhbz#2055183

* Wed Jul 21 2021 Honggang Li <honli@redhat.com> - 4.1.1-2
- fbtl-posix: link to common_ompio
- Require environment(modules)
- Revert upstream commit c36d7459b6331c4da82
- Resolves: rhbz#1974780, rhbz#1971771

* Wed Jun 09 2021 Honggang Li <honli@redhat.com> - 4.1.1-1
- Update to upstream v4.1.1 release
- Sync with Fedora build
- Resolves: rhbz#1928631, rhbz#1920801

* Wed Jan 27 2021 Honggang Li <honli@redhat.com> - 4.0.5-3
- disable gcc built-in atomics
- Resolves: rhbz#1921262

* Tue Nov 17 2020 Honggang Li <honli@redhat.com> - 4.0.5-2
- Rebuild against ucx-1.9 and libfabric-1.11.1
- Resolves: rhbz#1892128

* Mon Oct 12 2020 Honggang Li <honli@redhat.com> - 4.0.5-1
- Update to upstream v4.0.5 release
- Build against hwloc-2.2
- Resolves: rhbz#1850088,rhbz#1855197

* Tue Jul 28 2020 Honggang Li <honli@redhat.com> - 4.0.3-3
- Fix module load overwrites system MANPATH
- Resolves: rhbz#1858519

* Tue May 12 2020 Honggang Li <honli@redhat.com> - 4.0.3-1
- Update to upstream v4.0.3 release
- Resolves: rhbz#1817834

* Sun Jan 19 2020 Honggang Li <honli@redhat.com> - 4.0.2-2
- Rebuild against ucx-1.6
- Resolves: rhbz#1791483

* Wed Oct 16 2019 Jarod Wilson <jarod@redhat.com> - 4.0.2-1
- Update to upstream v4.0.2 release
- Resolves: rhbz#1725631

* Thu Aug 01 2019 Jarod Wilson <jarod@redhat.com> - 4.0.1-3
- Actually enable UCX support
- Resolves: rhbz#1642942

* Wed Jun 19 2019 Jarod Wilson <jarod@redhat.com> - 4.0.1-2
- Bump and rebuild for newer opensm
- Resolves: rhbz#1717289

* Mon Apr 29 2019 Jarod Wilson <jarod@redhat.com> - 4.0.1-1
- Update to upstream v4.0.1 release
- Resolves: rhbz#1660623

* Tue Sep 25 2018 Jarod Wilson <jarod@redhat.com> - 3.1.2-5
- Update BR: opensm-devel min version and rebuild against opensm 3.3.21
- Resolves: rhbz#1630653

* Mon Sep 24 2018 Jarod Wilson <jarod@redhat.com> - 3.1.2-4
- Further tweaks to compile/linker flag usage
- Related: rhbz#1624157
- Move modulefiles under /etc like our other suppored mpi providers
- Resolves: rhbz#1632399

* Tue Sep 18 2018 Jarod Wilson <jarod@redhat.com> - 3.1.2-3
- Undo stripping/ignoring of distro-provided optimization flags
- Related: rhbz#1624157

* Wed Sep 12 2018 Jarod Wilson <jarod@redhat.com> - 3.1.2-2
- Additional tweaks to module paths, fix openmpi-devel R
- Related: rhbz#1623441

* Wed Sep 12 2018 Jarod Wilson <jarod@redhat.com> - 3.1.2-1
- Update to upstream 3.1.2 bug fix release
- Fix some paths in module file, strip out python2 bits
- Related: rhbz#1623441

* Thu Aug 30 2018 Jarod Wilson <jarod@redhat.com> - 3.1.1-2
- Bump and rebuild for autogen rpmbuild library dependency fixes
- Related: rhbz#1623441

* Mon Jul 02 2018 Jarod Wilson <jarod@redhat.com> - 3.1.1-1
- Update to upstream 3.1.1 bug fix release
- Drop BR: on deprecated infinipath-psm

* Thu May 31 2018 Jarod Wilson <jarod@redhat.com> - 3.1.0-1
- Update to upstream 3.1.0 release
- Use external pmix and libevent

* Thu May 17 2018 Charalampos Stratakis <cstratak@redhat.com> - 2.1.1-11
- Do not build the python2 subpackage on EL > 7

* Wed May 09 2018 Troy Dawson <tdawson@redhat.com> - 2.1.1-10
- Build with rdma-core-devel instead of libibcm-devel

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2.1.1-9
- Escape macros in %%changelog

* Mon Feb 05 2018 Orion Poplawski <orion@cora.nwra.com> - 2.1.1-8
- Rebuild for rdma-core 16.2

* Wed Jan 31 2018 Christoph Junghans <junghans@votca.org> - 2.1.1-7
- Rebuild for gfortran-8

* Fri Jan 12 2018 Iryna Shcherbina <ishcherb@redhat.com> - 2.1.1-6
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Wed Aug 23 2017 Adam Williamson <awilliam@redhat.com> - 2.1.1-5
- Disable RDMA support on 32-bit ARM (#1484155)
- Disable hanging opal_fifo test on ppc64le (gh #2526 / #2966)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Wed Jul 19 2017 Orion Poplawski <orion@cora.nwra.com> - 2.1.1-2
- Provide pkgconfig files in the main namespace as well (1471512)

* Fri May 12 2017 Orion Poplawski <orion@cora.nwra.com> - 2.1.1-1
- Update to 2.1.1

* Thu May 4 2017 Orion Poplawski <orion@cora.nwra.com> - 2.1.0-1
- Update to 2.1.0
