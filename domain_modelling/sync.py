import hashlib
import os
import shutil
from pathlib import Path

BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def sync_old(source, dest):
    # walk the source folder and build a dict of hashes and filenames
    source_hashes = {}
    for folder, _, files in os.walk(source):
        for filename in files:
            source_hashes[hash_file(Path(folder, filename))] = filename

    # keep track of the files we've found in target
    seen = set()

    # walk the target folder and get the hashes and filenames
    for folder, _, files in os.walk(dest):
        for filename in files:
            dest_path = Path(folder) / filename
            dest_hash = hash_file(dest_path)
            seen.add(dest_hash)

            # if there's a file in target that's not in source, delete it
            if dest_hash not in source_hashes:
                dest_path.remove()

            # if there's a file in target that has a different path in source, move it to the correct path
            elif dest_hash in source_hashes and filename != source_hashes[dest_hash]:
                shutil.move(dest_path, Path(folder) / source_hashes[dest_hash])

    # for every file that appears in source but not in target, copy it to target
    for src_hash, filename in source_hashes.items():
        if src_hash not in seen:
            shutil.copy(Path(source) / filename, Path(dest) / filename)


def sync(reader, filesystem, source, dst):
    # imperative shell step 1, gather inputs
    source_hashes = reader(source)
    dst_hashes = reader(dst)

    for sha, filename in source_hashes.items():
        if sha not in dst_hashes:
            sourcepath = Path(source, filename)
            destpath = Path(dst, filename)
            filesystem.copy(sourcepath, destpath)
        elif filename != dst_hashes[sha]:
            filesystem.move(Path(dst, dst_hashes[sha]), Path(dst, filename))

    for sha, filename in dst_hashes.items():
        if sha not in source_hashes:
            filesystem.delete(Path(dst, filename))


def read_paths_and_hashes(path):
    hashes = {}
    for folder, _, files in os.walk(path):
        for filename in files:
            hashes[hash_file(Path(folder, filename))] = filename
    return hashes


def determine_actions(source_hashes, dst_hashes, source_folder, dst_folder):
    for sha, filename in source_hashes.items():
        if sha not in dst_hashes:
            sourcepath = Path(source_folder, filename)
            destpath = Path(dst_folder, filename)
            yield "COPY", sourcepath, destpath
        elif filename != dst_hashes[sha]:
            yield "MOVE", Path(dst_folder, dst_hashes[sha]), Path(dst_folder, filename)

    for sha, filename in dst_hashes.items():
        if sha not in source_hashes:
            yield "DELETE", Path(dst_folder, filename)
