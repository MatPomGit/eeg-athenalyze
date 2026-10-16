using System;
using BlueMuse.Athena;

// These are test-only dependency shims needed to compile the untouched upstream
// AthenaDecoders.cs without its WPF application. Values match the audited protocol.
namespace BlueMuse.Athena
{
    public static class Constants
    {
        public const double MUSE_ATHENA_EEG_MIDPOINT = 8192.0;
        public const double MUSE_ATHENA_EEG_SCALE_FACTOR = 1450.0 / 16383.0;
        public const int MUSE_ATHENA_IMU_CHANNEL_COUNT = 6;
        public const int MUSE_ATHENA_IMU_SAMPLE_COUNT = 3;
        public const int MUSE_ACCELEROMETER_CHANNEL_COUNT = 3;
        public const double MUSE_ACCELEROMETER_SCALE_FACTOR = 0.00006103515625;
        public const double MUSE_ATHENA_GYROSCOPE_SCALE_FACTOR = -0.007476806640625;
        public const int MUSE_ATHENA_OPTICS_CHANNEL_COUNT = 16;
        public const double MUSE_ATHENA_BATTERY_SCALE_FACTOR = 1.0 / 512.0;
    }
    public static class AthenaPacketParser
    {
        public const byte TAG_OPTICS_4CH = 0x34;
        public const byte TAG_OPTICS_8CH = 0x35;
        public const byte TAG_OPTICS_16CH = 0x36;
    }
}

public static class Program
{
    private static readonly (string Name, string Hex, int[] Codes)[] Cases =
    {
        ("rails", "004000f0ff018001a0ffffffab00004000f0ff018001a0ffffffab00",
          new [] {0,1,8191,8192,8193,16382,16383,42,0,1,8191,8192,8193,16382,16383,42}),
        ("sample-major", "640032c0124006654032d0124406668032e012480667c032f0124c06",
          new [] {100,200,300,400,101,201,301,401,102,202,302,402,103,203,303,403}),
        ("reversed-logical", "90014b800c900191414b900c940192814ba00c980193c14bb00c9c01",
          new [] {400,300,200,100,401,301,201,101,402,302,202,102,403,303,203,103}),
        ("alternating", "00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff00c0ff0f00fcff",
          new [] {0,16383,0,16383,0,16383,0,16383,0,16383,0,16383,0,16383,0,16383}),
    };
    public static int Main()
    {
        int checkedSamples = 0;
        foreach (var test in Cases)
        {
            byte[] payload = Convert.FromHexString(test.Hex);
            if (payload.Length != 28) throw new Exception("Incorrect fixture length");
            foreach (int channels in new [] {4,8})
            {
                int samples = 16/channels;
                double[,] actual = AthenaDecoders.DecodeEEG(payload, channels, samples);
                if (actual.GetLength(0) != samples || actual.GetLength(1) != channels)
                    throw new Exception($"Shape mismatch in {test.Name}");
                for (int i = 0; i < samples; i++)
                for (int j = 0; j < channels; j++)
                {
                    int raw = test.Codes[i*channels+j];
                    double expected = ((double)raw - 8192.0) * (1450.0/16383.0);
                    if (Math.Abs(actual[i,j] - expected) > 1e-10)
                        throw new Exception($"Mismatch: {test.Name} EEG{channels} [{i},{j}], raw={raw}, observed={actual[i,j]}, expected={expected}");
                    checkedSamples++;
                }
            }
        }
        Console.WriteLine($"ORIGINAL BLUEMUSE DecodeEEG PASS: {Cases.Length} frozen vectors x 2 layouts x 16 codes = {checkedSamples} values");
        return 0;
    }
}
