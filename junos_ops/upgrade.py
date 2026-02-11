"""upgrade 系機能: パッケージ転送・インストール・ロールバック・リブート・バージョン管理"""

from looseversion import LooseVersion
from jnpr.junos.exception import (
    ConnectError,
    RpcError,
    RpcTimeoutError,
)
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.fs import FS
from jnpr.junos.utils.sw import SW
from lxml import etree
from ncclient.operations.errors import TimeoutExpiredError
import argparse
import datetime
import re
from logging import getLogger

from junos_ops import common

logger = getLogger(__name__)


def delete_snapshots(dev) -> bool:
    """EX/QFXシリーズのスナップショットを全削除する

    :return: True=エラー, False=正常（SWITCH以外は何もせず False）
    """
    if dev.facts.get("personality") != "SWITCH":
        return False

    if common.args.dry_run:
        print("dry-run: request system snapshot delete *")
        return False

    try:
        rpc = dev.rpc.request_snapshot(delete="*", dev_timeout=60)
        xml_str = etree.tostring(rpc, encoding="unicode")
        logger.debug(f"delete_snapshots: {xml_str}")
        print("copy: snapshot delete successful")
    except RpcError as e:
        logger.warning(f"snapshot delete: RpcError: {e}")
        print(f"copy: snapshot delete skipped (RpcError: {e})")
    except RpcTimeoutError as e:
        logger.warning(f"snapshot delete: RpcTimeoutError: {e}")
        print(f"copy: snapshot delete skipped (RpcTimeoutError: {e})")
    except Exception as e:
        logger.warning(f"snapshot delete: {e}")
        print(f"copy: snapshot delete skipped ({e})")
    return False


def copy(hostname, dev):
    if common.args.debug:
        print("copy: start")
    if common.args.force:
        if common.args.debug:
            print("copy: force copy")
    else:
        if check_running_package(hostname, dev):
            print("Already Running, COPY Skip.")
            return False
        if check_remote_package(hostname, dev):
            print("remote package is already copied successfully")
            return False

    # request-system-storage-cleanup
    if common.args.dry_run:
        print("dry-run: request system storage cleanup")
    else:
        try:
            rpc = dev.rpc.request_system_storage_cleanup(
                no_confirm=True, dev_timeout=60
            )
            # default dev_timeout is 30 seconds, but it's not enough QFX series.
            xml_str = etree.tostring(rpc, encoding="unicode")
            if common.args.debug:
                print("copy: request-system-storage-cleanup=", xml_str)
            if xml_str.find("<success/>") >= 0:
                print("copy: system storage cleanup successful")
            else:
                print("copy: system storage cleanup failed")
                return True
        except RpcError as e:
            print("system storage cleanup failure caused by RpcError:", e)
            return True
        except RpcTimeoutError as e:
            print("system storage cleanup failure caused by RpcTimeoutError:", e)
            return True
        except Exception as e:
            print(e)
            return True

    # EX/QFXシリーズ: スナップショット削除でディスク容量を確保
    delete_snapshots(dev)

    # copy
    if common.args.dry_run:
        print(
            "dry-run: scp(checksum:%s) %s %s:%s"
            % (
                common.config.get(hostname, "hashalgo"),
                get_model_file(hostname, dev.facts["model"]),
                hostname,
                common.config.get(hostname, "rpath"),
            )
        )
        ret = False
    else:
        try:
            sw = SW(dev)
            result = sw.safe_copy(
                get_model_file(hostname, dev.facts["model"]),
                remote_path=common.config.get(hostname, "rpath"),
                progress=True,
                cleanfs=True,
                cleanfs_timeout=300,  # default 300
                checksum=get_model_hash(hostname, dev.facts["model"]),
                checksum_timeout=1200,  # default 300
                checksum_algorithm=common.config.get(hostname, "hashalgo"),
                force_copy=common.args.force,
            )
            if result:
                if common.args.debug:
                    print("copy: successful")
                ret = False
            else:
                if common.args.debug:
                    print("copy: failed")
                ret = True
        except TimeoutExpiredError as e:
            print("Copy failure caused by TimeoutExpiredError:", e)
            ret = True
        except RpcTimeoutError as e:
            print("Copy failure caused by RpcTimeoutError:", e)
            return True
        except Exception as e:
            print(e)
            ret = True

    if common.args.debug:
        print("copy: end", ret)
    return ret


def rollback(hostname, dev):
    if common.args.dry_run:
        print("dry-run: request system software rollback")
    else:
        try:
            rpc = dev.rpc.request_package_rollback({"format": "text"}, dev_timeout=120)
            # default dev_timeout is 30 seconds, but it's not enough SRX4600, MX5 and QFX5110.
            xml_str = etree.tostring(rpc, encoding="unicode")
            if common.args.debug:
                print("rollback: rpc=", rpc, "xml_str=", xml_str)
            if (
                xml_str.find("Deleting bootstrap installer") >= 0  # MX
                or xml_str.find("NOTICE: The 'pending' set has been removed") >= 0  # EX
                or xml_str.find("will become active at next reboot") >= 0  # SRX3xx
                or xml_str.find("Rollback of staged upgrade succeeded") >= 0  # SRX1500
                or xml_str.find("There is NO image for ROLLBACK") >= 0  # SRX4600
            ):
                print(f"rollback: request system software rollback successful:\n{xml_str}")
            else:
                print(f"rollback: request system software rollback failed:\n{xml_str}")
                return True
        except RpcError as e:
            print("request system software rollback failure caused by RpcError:", e)
            return True
        except RpcTimeoutError as e:
            print(
                "request system software rollback failure caused by RpcTimeoutError:",
                e,
            )
            return True
        except Exception as e:
            print(e)
            return True
    return False


def clear_reboot(dev) -> bool:
    # clear system reboot
    if common.args.dry_run:
        print("\tdry-run: clear system reboot")
    else:
        try:
            rpc = dev.rpc.clear_reboot({"format": "text"})
            xml_str = etree.tostring(rpc, encoding="unicode")
            logger.debug(f"{rpc=} {xml_str=}")
            if (
                xml_str.find("No shutdown/reboot scheduled.") >= 0
                or xml_str.find("Terminating...") >= 0
            ):
                logger.debug("clear reboot schedule successful")
                print("\tclear reboot schedule successful")
            else:
                logger.debug("clear reboot schedule failed")
                print("\tclear reboot schedule failed")
                return True
        except RpcError as e:
            logger.error(f"Clear reboot failure caused by RpcError: {e}")
            return True
        except RpcTimeoutError as e:
            logger.error(f"Clear reboot failure caused by RpcTimeoutError: {e}")
            return True
        except Exception as e:
            logger.error(e)
            return True
    return False


def install(hostname, dev):
    if common.args.debug:
        print("install: start")
    if common.args.force:
        if common.args.debug:
            print("install: force install")
    else:
        if check_running_package(hostname, dev):
            print("Already Running, INSTALL Skip.")
            return False

    pending = get_pending_version(hostname, dev)
    logger.debug(f"{pending=}")
    if pending is not None:
        planning = get_planning_version(hostname, dev)
        logger.debug(f"{planning=}")
        ret = compare_version(pending, planning)
        logger.debug(f"install: compare_version={ret}")
        if ret == 1:
            logger.debug(f"{pending=} > {planning=} : No need install.")
            print(f"\t{pending=} > {planning=} : No need install.")
        elif ret == -1:
            logger.debug(f"{pending=} < {planning=} : NEED INSTALL.")
            print(f"\t{pending=} < {planning=} : NEED INSTALL.")
        elif ret == 0:
            logger.debug(f"{pending=} = {planning=} : No need install.")
            print(f"\t{pending=} = {planning=} : No need install.")

        if ret == 1 or ret == 0:
            if common.args.force:
                # force INSTALL
                pass
            else:
                return False

        ret = rollback(hostname, dev)
        if ret:
            if common.args.force:
                pass
            else:
                return True

    # EX series delete remote package after installed. so, must check first pending version before copy.
    if common.args.dry_run and (common.args.copy or common.args.update):
        print("dry-run: skip remote package check")
    elif check_remote_package(hostname, dev) is not True and common.args.install:
        # install() does not copy
        logger.info("remote package file not found. Please consider --copy before --install")
        return True

    if copy(hostname, dev):
        return True

    if clear_reboot(dev):
        return True

    # request system configuration rescue save
    if common.args.dry_run:
        print("dry-run: request system configuration rescue save")
    else:
        cu = Config(dev)
        try:
            ret = cu.rescue("save")
            if ret:
                print("install: rescue config save successful")
            else:
                print("install: rescue config save failed")
                return True
        except ValueError as e:
            print("wrong rescue action", e)
            return True
        except Exception as e:
            print(e)
            return True

    # request system software add ...
    if common.args.dry_run:
        print(
            "dry-run: request system software add %s/%s"
            % (
                common.config.get(hostname, "rpath"),
                get_model_file(hostname, dev.facts["model"]),
            )
        )
        ret = False
    else:
        sw = SW(dev)
        status, msg = sw.install(
            get_model_file(hostname, dev.facts["model"]),
            remote_path=common.config.get(hostname, "rpath"),
            progress=True,
            validate=True,
            cleanfs=True,
            no_copy=True,
            issu=False,
            nssu=False,
            timeout=2400,  # default 1800
            cleanfs_timeout=300,  # default 300
            checksum=get_model_hash(hostname, dev.facts["model"]),
            checksum_timeout=1200,  # default 300
            checksum_algorithm=common.config.get(hostname, "hashalgo"),
            force_copy=common.args.force,
            all_re=True,
        )
        del sw
        logger.debug(f"{msg=}")
        if status:
            logger.info("install successful")
            ret = False
        else:
            logger.info("install failed")
            ret = True

    logger.debug(f"end {ret=}")
    return ret


def get_model_file(hostname, model):
    try:
        return common.config.get(hostname, model.lower() + ".file")
    except Exception as e:
        logger.error(f"{hostname}: {model.lower()}.file not found in recipe: {e}")
        raise


def get_model_hash(hostname, model):
    try:
        return common.config.get(hostname, model.lower() + ".hash")
    except Exception as e:
        logger.error(f"{hostname}: {model.lower()}.hash not found in recipe: {e}")
        raise


def get_hashcache(hostname, file):
    with common.config_lock:
        if common.config.has_section(hostname) is False:
            return None
        if common.config.has_option(hostname, file + "hashcache"):
            hashcache = common.config.get(hostname, file + "hashcache")
        else:
            hashcache = None
        return hashcache


def set_hashcache(hostname, file, value):
    with common.config_lock:
        if common.config.has_section(hostname) is False:
            # "localhost"
            common.config.add_section(hostname)
        common.config.set(hostname, file + "hashcache", value)


def check_local_package(hostname, dev):
    """check local package
    :returns:
       * ``True`` file found, checksum correct.
       * ``False`` file found, checksum incorrect.
       * ``None`` file not found.
    """
    # local package check
    # model, file, hash, algo
    model = dev.facts["model"]
    file = get_model_file(hostname, model)
    pkg_hash = get_model_hash(hostname, model)
    if len(file) == 0 or len(pkg_hash) == 0:
        return None
    algo = common.config.get(hostname, "hashalgo")
    sw = SW(dev)
    if get_hashcache("localhost", file) == pkg_hash:
        print(f"  - local package: {file} is found. checksum(cache) is OK.")
        return True
    ret = None
    try:
        val = sw.local_checksum(file, algorithm=algo)
        if val == pkg_hash:
            print(f"  - local package: {file} is found. checksum is OK.")
            set_hashcache("localhost", file, val)
            ret = True
        else:
            print(f"  - local package: {file} is found. checksum is BAD. COPY AGAIN!")
            ret = False
    except FileNotFoundError as e:
        print(f"  - local package: {file} is not found.")
        logger.debug(e)
    except Exception as e:
        logger.error(e)
    del sw
    return ret


def check_remote_package(hostname, dev):
    """check remote package
    :returns:
       * ``True`` file found, checksum correct.
       * ``False`` file found, checksum incorrect.
       * ``None`` file not found.
    """
    # remote package check
    # model, file, hash, algo
    model = dev.facts["model"]
    file = get_model_file(hostname, model)
    pkg_hash = get_model_hash(hostname, model)
    if len(file) == 0 or len(pkg_hash) == 0:
        return None
    algo = common.config.get(hostname, "hashalgo")
    sw = SW(dev)
    ret = None
    if get_hashcache(hostname, file) == pkg_hash:
        print(f"  - remote package: {file} is found. checksum(cache) is OK.")
        return True
    try:
        val = sw.remote_checksum(
            common.config.get(hostname, "rpath") + "/" + file, algorithm=algo
        )
        if val is None:
            print(f"  - remote package: {file} is not found.")
        elif val == pkg_hash:
            print(f"  - remote package: {file} is found. checksum is OK.")
            set_hashcache(hostname, file, val)
            ret = True
        else:
            print(f"  - remote package: {file} is found. checksum is BAD. COPY AGAIN!")
            ret = False
    except RpcError as e:
        logger.error("Unable to remote checksum: {0}".format(e))
    except Exception as e:
        logger.error(e)
    del sw
    return ret


def list_remote_path(hostname, dev):
    # list remote path
    if common.args.debug:
        print("list_remote_path: start")
    # file list /var/tmp/
    fs = FS(dev)
    rpath = common.config.get(hostname, "rpath")
    dir_info = fs.ls(path=rpath, brief=False)
    print(dir_info.get("path") + ":")
    a = dir_info.get("files")
    if common.args.list_format == "short":
        for i in a.keys():
            b = a.get(i)
            if b.get("type") == "file":
                print(b.get("path"))
            else:
                print(b.get("path") + "/")
    else:
        for i in a.keys():
            b = a.get(i)
            print(
                "%s %s %9d %s %s"
                % (
                    b.get("permissions_text"),
                    b.get("owner"),
                    b.get("size"),
                    b.get("ts_date"),
                    b.get("path"),
                )
            )
        print("total files: %d" % dir_info.get("file_count"))
    if common.args.debug:
        print("list_remote_path: end")
    return dir_info


def dry_run(hostname, dev):
    if common.args.debug:
        print("dry-run: start")
        print("hostname: ", dev.facts["hostname"])
        print("model: ", dev.facts["model"])
        print("file:", get_model_file(hostname, dev.facts["model"]))
        print("hash:", get_model_hash(hostname, dev.facts["model"]))
        print("algo:", common.config.get(hostname, "hashalgo"))
    # show hostname, model, file, hash and algo
    # local package check
    local = check_local_package(hostname, dev)
    # remote package check
    remote = check_remote_package(hostname, dev)
    if common.args.debug:
        print("dry-run: end")
    if local and remote:
        return True
    else:
        return False


def check_running_package(hostname, dev):
    """compare running version with planning version
    :returns:
       * ``True`` same(correct)
       * ``False`` diffrent(incorrect)
    """
    if common.args.debug:
        print("check_running_package: start")
    ret = None
    ver = dev.facts["version"]
    rever = re.sub(r"\.", r"\\.", ver)
    if common.args.debug:
        print("check_running_package: ver", ver)
        print("check_running_package: rever", rever)
    m = re.search(rever, get_model_file(hostname, dev.facts["model"]))
    if common.args.debug:
        print("check_running_package: m", m)
    if m is None:
        # unmatch(different version)
        ret = False
    else:
        # match(same version)
        ret = True
    if common.args.debug:
        print("check_running_package: end")
    return ret


def compare_version(left: str, right: str) -> int | None:
    """compare version left and right

    :param left: version left string, ex 18.4R3-S9.2
    :param right: version right string, ex 18.4R3-S10

    :return:  1 if left  > right
              0 if left == right
             -1 if left  < right
    """
    if common.args.debug:
        print(f"compare_version: left={left}, right={right}.")
    if left is None or right is None:
        return None
    if LooseVersion(left.replace("-S", "00")) > LooseVersion(right.replace("-S", "00")):
        return 1
    if LooseVersion(left.replace("-S", "00")) < LooseVersion(right.replace("-S", "00")):
        return -1
    return 0


def get_pending_version(hostname, dev) -> str:
    """
    :returns:
       * ``None`` not exist
       * ``str`` pending version string
    """
    pending = None
    try:
        rpc = dev.rpc.get_software_information({"format": "text"})
        xml_str = etree.tostring(rpc, encoding="unicode")
        if common.args.debug:
            print(
                "get_pending_version: rpc=", rpc, "type(xml_str)=", type(xml_str), "xml_str=", xml_str
            )
        if dev.facts["personality"] == "SWITCH":
            if common.args.debug:
                print("get_pending_version: EX/QFX series")
            # Pending: 18.4R3-S10
            m = re.search(r"^Pending:\s(.*)$", xml_str, re.MULTILINE)
            if m is not None:
                pending = m.group(1)
        elif dev.facts["personality"] == "MX":
            if common.args.debug:
                print("get_pending_version: MX series")
            # JUNOS Installation Software [18.4R3-S10]
            m = re.search(
                r"^JUNOS\sInstallation\sSoftware\s\[(.*)\]$", xml_str, re.MULTILINE
            )
            if m is not None:
                pending = m.group(1)
        elif dev.facts["personality"] == "SRX_BRANCH":
            # Dual Partition - SRX300, SRX345
            if common.args.debug:
                print("get_pending_version: SRX_BRANCH series")
            xml = dev.rpc.get_snapshot_information(media="internal")
            if common.args.debug:
                print(f"get_snapshot_information: xml={etree.dump(xml)}")
            primary = False
            for i in range(len(xml)):
                if common.args.debug:
                    print(
                        f"get_snapshot_information: i={i}, tag={xml[i].tag}, text={xml[i].text}"
                    )
                if (
                    xml[i].tag == "snapshot-medium"
                    and re.match(".*primary", xml[i].text, re.MULTILINE | re.DOTALL)
                    is not None
                ):
                    if common.args.debug:
                        print("primary find")
                    primary = True
                if (
                    primary
                    and xml[i].tag == "software-version"
                    and xml[i][0].tag == "package"
                    and xml[i][0][1].tag == "package-version"
                ):
                    pending = xml[i][0][1].text.strip()
                    break
        elif (
            dev.facts["personality"] == "SRX_MIDRANGE"
            or dev.facts["personality"] == "SRX_HIGHEND"
        ):
            # SRX1500, SRX4600
            if common.args.debug:
                print("get_pending_version: SRX_MIDRANGE or SRX_HIGHEND series")
            # show log install
            # upgrade_platform: Staging of /var/tmp/junos-srxentedge-x86-64-20.4R3.8-linux.tgz completed
            # &lt;package-result&gt;0&lt;/package-result&gt;
            try:
                rpc = dev.rpc.get_log({"format": "text"}, filename="install")
                xml_str = etree.tostring(rpc, encoding="unicode")
                if common.args.debug:
                    print(
                        "get_pending_version: rpc=",
                        rpc,
                        "type(xml_str)=",
                        type(xml_str),
                        "xml_str=",
                        xml_str,
                    )
                if xml_str is not None:
                    # search from last <output> block
                    start = xml_str.rfind("&lt;output&gt;")
                    m = re.search(
                        r"upgrade_platform: Staging of /var/tmp/.*-(\d{2}\.\d.*\d).*\.tgz completed",
                        xml_str[start:],
                        re.MULTILINE,
                    )
                    if m is not None:
                        pending = m.group(1).strip()
                    m = re.search(
                        r"&lt;package-result&gt;(\d)&lt;/package-result&gt;",
                        xml_str[start:],
                        re.MULTILINE,
                    )
                    if m is not None:
                        if int(m.group(1)) == 0:
                            pass
                        else:
                            pending = None
            except Exception as e:
                print(e)
                return None
        else:
            print("Unknown personality:", dev.facts)
            return None
    except RpcError as e:
        print("Show version failure caused by RpcError:", e)
        return None
    except RpcTimeoutError as e:
        print("Show version failure caused by RpcTimeoutError:", e)
        return None
    except Exception as e:
        print(e)
        return None
    return pending


def get_planning_version(hostname, dev) -> str:
    planning = None
    f = get_model_file(hostname, dev.facts["model"])
    m = re.search(r".*-(\d{2}\.\d.*\d).*\.tgz", f)
    if m is not None:
        planning = m.group(1).strip()
    else:
        logger.debug("get_planning_version: planning version is not found")
    return planning


def get_reboot_information(hostname, dev):
    """show system reboot
    :return: halt requested by exadmin at Sun Dec 19 08:30:00 2021
             shutdown requested by exadmin at Sun Dec 12 08:30:00 2021
             reboot requested by exadmin at Sun Dec  5 01:00:00 2021
             No shutdown/reboot scheduled.
    """
    try:
        rpc = dev.rpc.get_reboot_information({"format": "text"})
    except RpcError as e:
        logger.error("Show version failure caused by RpcError:", e)
        return None
    except RpcTimeoutError as e:
        logger.error("Show version failure caused by RpcTimeoutError:", e)
        return None
    except Exception as e:
        logger.error(e)
        return None
    xml_str = etree.tostring(rpc, encoding="unicode")
    if common.args.debug:
        print(xml_str)
    m = re.search(
        r"((halt|shutdown|reboot)\srequested\sby\s.*\sat\s(.*\d)|No\sshutdown\/reboot\sscheduled\.)",
        xml_str,
        re.MULTILINE,
    )
    if m is None:
        return None
    return m.group(1)


def get_commit_information(dev):
    """最新コミット情報を取得する

    :return: (epoch_seconds, datetime_str, user, client) のタプル、または None
    """
    try:
        xml = dev.rpc.get_commit_information()
    except RpcError as e:
        logger.error(f"get_commit_information: RpcError: {e}")
        return None
    except RpcTimeoutError as e:
        logger.error(f"get_commit_information: RpcTimeoutError: {e}")
        return None
    except Exception as e:
        logger.error(f"get_commit_information: {e}")
        return None

    for elem in xml:
        if elem.tag == "commit-history":
            seq = elem.find("sequence-number")
            if seq is not None and seq.text == "0":
                dt = elem.find("date-time")
                user = elem.find("user")
                client = elem.find("client")
                if dt is not None:
                    epoch = int(dt.get("seconds", "0"))
                    return (epoch, dt.text, user.text if user is not None else "", client.text if client is not None else "")
    return None


def get_rescue_config_time(dev):
    """rescue config ファイルの更新時刻（epoch秒）を取得する

    :return: epoch_seconds (int) または None（ファイルなし・エラー時）
    """
    try:
        xml = dev.rpc.file_list(path="/config/rescue.conf.gz", detail=True)
    except RpcError as e:
        logger.error(f"get_rescue_config_time: RpcError: {e}")
        return None
    except RpcTimeoutError as e:
        logger.error(f"get_rescue_config_time: RpcTimeoutError: {e}")
        return None
    except Exception as e:
        logger.error(f"get_rescue_config_time: {e}")
        return None

    # ファイルが存在しない場合は <output> にエラーメッセージが入る
    file_info = xml.find(".//file-information")
    if file_info is None:
        return None
    file_date = file_info.find("file-date")
    if file_date is None:
        return None
    seconds = file_date.get("seconds")
    if seconds is None:
        return None
    return int(seconds)


def show_version(hostname, dev):
    """show version
    show running version
    show pending version
    check for updated
    suggest action to copy, install, reboot or beer.
    """

    logger.debug("start")

    print("  - hostname:", dev.facts["hostname"])
    print("  - model:", dev.facts["model"])
    running = dev.facts["version"]
    print("  - running version:", running)

    # compare with planning version
    planning = get_planning_version(hostname, dev)
    print("  - planning version:", planning)
    ret = compare_version(running, planning)
    if ret == 1:
        print(f"    - {running=} > {planning=}")
    elif ret == -1:
        print(f"    - {running=} < {planning=}")
    elif ret == 0:
        print(f"    - {running=} = {planning=}")
    # compare with pending version
    pending = get_pending_version(hostname, dev)
    print("  - pending version:", pending)
    ret = compare_version(running, pending)
    if ret == 1:
        print(f"    - {running=} > {pending=} : Do you want to rollback?")
    elif ret == -1:
        print(f"    - {running=} < {pending=} : Please plan to reboot.")
    elif ret == 0:
        print(f"    - {running=} = {pending=}")

    # コミット情報と config 変更検出
    commit_info = get_commit_information(dev)
    if commit_info is not None:
        commit_epoch, commit_dt_str, commit_user, commit_client = commit_info
        print(f"  - last commit: {commit_dt_str} by {commit_user} via {commit_client}")
        if pending is not None:
            rescue_epoch = get_rescue_config_time(dev)
            if rescue_epoch is None or commit_epoch > rescue_epoch:
                print(f"    - WARNING: config modified after firmware install. Re-install will run on reboot.")

    # local package check
    local = check_local_package(hostname, dev)

    # remote package check
    remote = check_remote_package(hostname, dev)

    rebooting = get_reboot_information(hostname, dev)
    if rebooting is not None:
        print(f"  - {rebooting}")

    logger.debug("end")

    return False


def check_and_reinstall(hostname, dev) -> bool:
    """pending version がある場合、config が install 後に変更されていたら再インストールする

    :return: True=エラー, False=正常（再インストール不要含む）
    """
    pending = get_pending_version(hostname, dev)
    if pending is None:
        logger.debug("check_and_reinstall: no pending version, skip")
        return False

    commit_info = get_commit_information(dev)
    if commit_info is None:
        logger.debug("check_and_reinstall: cannot get commit information, skip")
        return False

    commit_epoch, commit_dt_str, commit_user, commit_client = commit_info
    rescue_epoch = get_rescue_config_time(dev)

    if rescue_epoch is not None and commit_epoch <= rescue_epoch:
        logger.debug("check_and_reinstall: config not modified after rescue save, skip")
        return False

    # config が rescue config 保存後に変更されている（または rescue config がない）
    if rescue_epoch is None:
        print(f"\tWARNING: rescue config not found. Re-installing firmware with current config.")
    else:
        print(f"\tWARNING: config modified after firmware install ({commit_dt_str} by {commit_user} via {commit_client}).")
        print(f"\tRe-installing firmware to validate current config.")

    if common.args.dry_run:
        print("\tdry-run: re-install and rescue config save skipped")
        return False

    # rescue config 再保存
    cu = Config(dev)
    try:
        ret = cu.rescue("save")
        if ret:
            print("\tre-install: rescue config save successful")
        else:
            print("\tre-install: rescue config save failed")
            return True
    except Exception as e:
        logger.error(f"check_and_reinstall: rescue save failed: {e}")
        return True

    # 再インストール（validation 付き）
    try:
        sw = SW(dev)
        status, msg = sw.install(
            get_model_file(hostname, dev.facts["model"]),
            remote_path=common.config.get(hostname, "rpath"),
            progress=True,
            validate=True,
            cleanfs=False,
            no_copy=True,
            issu=False,
            nssu=False,
            timeout=2400,
            checksum=get_model_hash(hostname, dev.facts["model"]),
            checksum_timeout=1200,
            checksum_algorithm=common.config.get(hostname, "hashalgo"),
            all_re=True,
        )
        del sw
        logger.debug(f"check_and_reinstall: {msg=}")
        if status:
            print("\tre-install: successful")
            return False
        else:
            print(f"\tre-install: failed: {msg}")
            return True
    except Exception as e:
        logger.error(f"check_and_reinstall: install failed: {e}")
        return True


def reboot(hostname: str, dev, reboot_dt: datetime.datetime):
    logger.debug(f"{reboot_dt=}")
    try:
        rpc = dev.rpc.get_reboot_information({"format": "text"})
    except ConnectError as err:
        logger.error(f"{err=}")
        return 2
    xml_str = etree.tostring(rpc, encoding="unicode")
    logger.debug(f"{xml_str=}")
    if xml_str.find("No shutdown/reboot scheduled.") >= 0:
        pass
    else:
        logger.debug("ANY SHUTDWON/REBOOT SCHEDULE EXISTS")
        match = re.search(r"^(\w+) requested by (\w+) at (.*)$", xml_str, re.MULTILINE)
        if len(match.groups()) == 3:
            dt = datetime.datetime.strptime(match.group(3), "%a %b %d %H:%M:%S %Y")
            print(f"\t{match.group(1).upper()} SCHEDULE EXISTS AT {dt}")
            if common.args.force:
                logger.debug("force clear reboot")
                print("\tforce: clear reboot")
                if clear_reboot(dev):
                    return 3
            else:
                logger.debug("skip clear reboot")

    # config 変更検出 + 自動再インストール
    if check_and_reinstall(hostname, dev):
        return 6

    # reboot
    at_str = reboot_dt.strftime("%y%m%d%H%M")
    sw = SW(dev)
    try:
        if common.args.dry_run:
            msg = f"dry-run: reboot at {at_str}"
        else:
            msg = sw.reboot(at=at_str)
    except ConnectError as e:
        logger.error(f"{e=}")
        return 4
    except RpcError as e:
        logger.error(f"{e}")
        return 5
    print(f"\t{msg}")
    del sw

    dev.close()
    logger.debug("success")
    return 0


def yymmddhhmm_type(dt_str: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(dt_str, "%y%m%d%H%M")
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"{e}: {dt_str} must be yymmddhhmm format. ex. 2501020304"
        )


def load_config(hostname, dev, configfile) -> bool:
    """set コマンドファイルをロードしてコミットする

    commit フロー: lock → load → diff → commit_check → commit confirmed → confirm → unlock
    エラー時は rollback + unlock でクリーンアップ。

    :param hostname: ホスト名（表示用）
    :param dev: PyEZ Device インスタンス
    :param configfile: set コマンドファイルのパス
    :return: True=エラー, False=正常
    """
    cu = Config(dev)

    # config ロック取得
    try:
        cu.lock()
    except Exception as e:
        logger.error(f"{hostname}: config lock failed: {e}")
        print(f"\tconfig lock failed: {e}")
        return True

    try:
        # set コマンドファイル読み込み
        cu.load(path=configfile, format="set")

        # 差分確認
        diff = cu.diff()
        if diff is None:
            print("\tno changes")
            cu.unlock()
            return False

        cu.pdiff()

        # dry-run: diff 表示のみで終了
        if common.args.dry_run:
            print("\tdry-run: rollback (no commit)")
            cu.rollback()
            cu.unlock()
            return False

        # validation
        cu.commit_check()
        print("\tcommit check passed")

        # commit confirmed（自動ロールバック付き）
        confirm_timeout = getattr(common.args, "confirm_timeout", 1)
        cu.commit(confirm=confirm_timeout)
        print(f"\tcommit confirmed {confirm_timeout} applied")

        # 確定（タイマー解除）
        cu.commit()
        print("\tcommit confirmed, changes are now permanent")

    except Exception as e:
        logger.error(f"{hostname}: config push failed: {e}")
        print(f"\tconfig push failed: {e}")
        try:
            cu.rollback()
        except Exception:
            pass
        try:
            cu.unlock()
        except Exception:
            pass
        return True

    cu.unlock()
    return False
