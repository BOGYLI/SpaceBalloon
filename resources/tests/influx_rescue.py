import snappy

in_path = r"C:\Users\Nikocraft\Downloads\_00003.wal"
out_path = r"C:\Users\Nikocraft\Downloads\_00003.wal.v1"

count = 0
success = 0
failed = 0
with open(in_path, mode='rb') as in_file:
  with open(out_path, mode='wb') as out_file:
    while True:
      op_type = in_file.read(1) # first byte is an operation code

      if op_type == b"":
        print('file end', in_file.tell())
        break

      if op_type[0] == 1 or op_type[0] == 0: # use it to identify out-of-sync
        count += 1 # just for statistics
        length_b = in_file.read(4) # length of the field
        length = int.from_bytes(length_b, "big") # in my case they were big-endian
        print('id', count, 'op_type', op_type, 'length', length)
        d_raw = in_file.read(length)
        try:

          d = snappy.uncompress(d_raw) # a real test if the data is not corrupt

          # copy good data to a new file
          out_file.write(op_type)
          out_file.write(length_b)
          out_file.write(d_raw)

          success += 1

        except Exception as e:
          # the current entry wasn't readable, skip it
          
          failed += 1
          print('exception', e)

      else:
        print('id', count, 'unexpected op type', op_type, 'at file position', in_file.tell())
        # if this is your case and you expect more valid data in the file, you may try to re-sync here
        break

print('total entries found', count)
print('success', success)
print('failed', failed)
