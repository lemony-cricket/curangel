import os
import re
import argparse

from loguru import logger


class _DictionaryStorageAction(argparse.Action):
    def __call__(self, parser, namespace, values, *args):
        data = {}
        for value in values:
            if "=" not in value:
                err = f"{value}: key must be separated from value by '='"
                raise ValueError(err)
            key, value = value.split("=", 1)
            data[key.strip()] = value.strip()
        setattr(namespace, self.dest, data)


_ap = argparse.ArgumentParser()
_ap.add_argument("troot", type=str, metavar="template-root",
                 help="root of template file tree to expand")
_ap.add_argument("droot", type=str, metavar="destination-root",
                 help="destination for root of expanded file tree")
_ap.add_argument("subs", nargs="*", metavar="key=value",
                 action=_DictionaryStorageAction,
                 help="list of keys to replace with values")


def expand(template, destination, subs):
    if os.path.isdir(template):
        logger.info(f"expanding {template} into {destination}")
        for child in os.listdir(template):
            os.makedirs(destination, exist_ok=True)
            expand(os.path.join(template, child),
                   os.path.join(destination, child),
                   subs)
    elif os.path.isfile(template):
        name_exps = re.findall(r"%[^%]*%", destination)
        for name_exp in name_exps:
            name_exp_key = name_exp.strip("%")
            destination = destination.replace(name_exp, subs[name_exp_key])
        if os.path.exists(destination):
            if os.path.samefile(template, destination):
                logger.warning(f"not expanding over same file; check paths")
                return
        with open(template, "r") as tmpl_file:
            with open(destination, "w") as dest_file:
                content_t = tmpl_file.read()
                content_expr = f'f"""{content_t}"""'
                logger.info(f"expanding {template} into {destination}")
                dest_file.write(eval(content_expr, subs))
    elif not os.path.exists(template):
        raise FileNotFoundError(f"nothing exists at {template}")
    else:
        raise RuntimeError(f"unexpected error at {template}")


if __name__ == "__main__":
    args = _ap.parse_args()
    expand(args.troot, args.droot, args.subs)
