using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System;
using System.Text;

public class Sensor : MonoBehaviour
{
    public static float latitude;
    public static float longitude;
    public static float altitude;
    public static Quaternion attitude;
    public static bool gpsStarted = false;
    public static bool isProperCamera = true;
    private static LocationInfo location;
    private static WaitForSeconds second;

    public static Gyroscope m_Gyro;

    Socket data_sock = null;
    string IP = null;
    enum DataFormat : byte
    {
        EMPTY = 0x00,
        TEXT = 0x01,
        SENSOR = 0x02,
        DEST = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    private void Awake()
    {
        second = new WaitForSeconds(1.0f);
        IP = Loading.Instance.GetIP();
        data_sock = Loading.Instance.GetDatatSocket();
    }

    // Start is called before the first frame update
    IEnumerator Start()
    {
        if (!Input.location.isEnabledByUser)
        {
            SetText("loc", "GPS is not enabled");
            yield break;
        }

        Input.location.Start(1f, 1f);
        SetText("loc", "Awaiting initialization");

        int maxWait = 10;
        while (Input.location.status == LocationServiceStatus.Initializing && maxWait > 0)
        {
            yield return second;
            maxWait--;
        }

        if (maxWait < 1)
        {
            SetText("loc", "Timed out");
            yield break;
        }

        if (Input.location.status == LocationServiceStatus.Failed)
        {
            SetText("loc", "Unable to determine device location");
            yield break;
        }
        gpsStarted = true;
        SetText("loc", "ok");
        
        yield break;
    }

    void Update(){
        if(gpsStarted){
            location = Input.location.lastData;
            latitude = location.latitude;
            longitude = location.longitude;
            altitude = location.altitude;
        }
        int i;
        for (i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;
        m_Gyro = Input.gyro;
        attitude = m_Gyro.attitude;
        Vector3 m_Vector = attitude * Vector3.up;

        isProperCamera = true;

        // if Mobile is not in 45 to 135 degree, Send Message 
        if (!(Mathf.Abs(GetAngle(m_Vector, Vector3.up)) >= 45 && Mathf.Abs(GetAngle(m_Vector, Vector3.up)) <= 135))
        {
            isProperCamera = false;
        }
        float qw = attitude.w;
        float qx = attitude.x;
        float qy = attitude.y;
        float qz = attitude.z;

        float[] tmp = new float[7] { latitude, longitude, altitude, qw, qx, qy, qz };
        byte[] msg = new byte[tmp.Length * sizeof(float)];

        Buffer.BlockCopy(tmp, 0, msg, 0, msg.Length);
        buffer[0] = (byte)DataFormat.SENSOR;
        for (i = 0; i < Math.Min(buffer.Length - 2, msg.Length); i++)
            buffer[i + 1] = msg[i];
        buffer[i + 1] = ETX;
        data_sock.Send(buffer, 1024, SocketFlags.None);
    }

    void OnGUI()
    {
        // if User do not hold Camera properly
        if (!isProperCamera)
        {
            GUI.Label(new Rect(0, 0, Screen.width / 2, Screen.height / 2), "Please Hold the Camera Properly");
        }
    }

    public static void StopGPS()
    {
        if (Input.location.isEnabledByUser)
        {
            gpsStarted = false;
            Input.location.Stop();
        }
    }

    float GetAngle(Vector3 v1, Vector3 v2)
    {
        {
            return Mathf.Acos(Vector3.Dot(v1, v2) / Vector3.Magnitude(v1) / Vector3.Magnitude(v2)) * Mathf.Rad2Deg;
        }
    }

    void SetText(string name, string str)
    {
        GameObject debugText = GameObject.Find(name);
        if (debugText != null)
        {
            TextMesh textMesh = debugText.GetComponent("TextMesh") as TextMesh;
            if (textMesh != null)
            {
                textMesh.text = str;
            }
        }
    }
}
